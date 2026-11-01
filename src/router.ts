import { z } from 'zod';
import { OrbiError, parseConfig, type RouterConfig } from './config.js';
import { run, type Runner } from './process.js';

export const statusSchema = z.object({
  model: z.literal('RBR850'), firmware: z.string().min(1),
  uptimeSeconds: z.number().finite().nonnegative(),
  loadAverage: z.object({ oneMinute: z.number().finite().nonnegative(), fiveMinutes: z.number().finite().nonnegative(), fifteenMinutes: z.number().finite().nonnegative() }),
  memory: z.object({ totalBytes: z.number().int().positive(), availableBytes: z.number().int().nonnegative() }),
  wan: z.object({ interface: z.literal('eth4'), linkUp: z.boolean(), speedMbps: z.number().positive().nullable(), duplex: z.enum(['full', 'half']).nullable() }),
  observedAt: z.string().datetime(), source: z.literal('ssh'),
});
export type RouterStatus = z.infer<typeof statusSchema>;

const READ_STATUS = `set -eu
export LC_ALL=C
printf '%s\\n' '__ORBI_PLATFORM__'
cat /ntgr/platform_info.json
printf '\\n%s\\n' '__ORBI_VERSION__'
cat /etc/version
printf '\\n%s\\n' '__ORBI_ODM__'
cat /etc/odm_version
printf '\\n%s\\n' '__ORBI_UPTIME__'
cat /proc/uptime
printf '%s\\n' '__ORBI_LOAD__'
cat /proc/loadavg
printf '%s\\n' '__ORBI_MEMORY__'
cat /proc/meminfo
printf '%s\\n' '__ORBI_ETHERNET__'
ethtool eth4
`;

export function parseStatus(output: string): RouterStatus {
  try {
    const sections = new Map<string, string>();
    for (const match of output.matchAll(/^__ORBI_([A-Z]+)__\r?\n([\s\S]*?)(?=^__ORBI_|$(?![\s\S]))/gm)) {
      if (sections.has(match[1]!)) throw new Error('duplicate section');
      sections.set(match[1]!, match[2]!.trim());
    }
    const get = (name: string): string => { const value = sections.get(name); if (!value) throw new Error('missing section'); return value; };
    const platform = JSON.parse(get('PLATFORM'));
    if (platform.productName !== 'RBR850' || platform.wanIntf !== 'eth4') throw new Error('unsupported platform');
    const version = get('VERSION'); const odm = get('ODM');
    if (!/^\d+(?:\.\d+){3}$/.test(version) || !/^\d+(?:\.\d+){2}$/.test(odm)) throw new Error('invalid version');
    const number = (value: string): number => {
      if (!/^\d+(?:\.\d+)?$/.test(value)) throw new Error('invalid number');
      return Number(value);
    };
    const load = get('LOAD').split(/\s+/).slice(0, 3).map(number);
    if (load.length !== 3) throw new Error('missing load');
    const memory = get('MEMORY');
    const kib = (field: string): number => number(memory.match(new RegExp(`^${field}:\\s+(\\d+) kB$`, 'm'))?.[1] || '') * 1024;
    const totalBytes = kib('MemTotal'); const availableBytes = kib('MemAvailable');
    if (availableBytes > totalBytes) throw new Error('invalid memory');
    const ethernet = get('ETHERNET');
    const unique = (field: string): string | undefined => {
      const matches = [...ethernet.matchAll(new RegExp(`^\\s*${field}:\\s*(.*?)\\s*$`, 'gm'))];
      if (matches.length !== 1) throw new Error('missing or duplicate port field');
      return matches[0]![1];
    };
    const link = unique('Link detected');
    if (link !== 'yes' && link !== 'no') throw new Error('invalid link state');
    const speedText = unique('Speed'); const duplexText = unique('Duplex');
    const speed = /^(\d+)Mb\/s$/.exec(speedText || '')?.[1];
    const duplex = /^(Full|Half)$/.exec(duplexText || '')?.[1]?.toLowerCase();
    if (link === 'yes' && (!speed || !duplex)) throw new Error('missing live port metrics');
    return statusSchema.parse({
      model: platform.productName, firmware: `V${version}_${odm}`,
      uptimeSeconds: number(get('UPTIME').split(/\s+/)[0]!),
      loadAverage: { oneMinute: load[0], fiveMinutes: load[1], fifteenMinutes: load[2] },
      memory: { totalBytes, availableBytes },
      wan: { interface: 'eth4', linkUp: link === 'yes', speedMbps: speed ? number(speed) : null, duplex: duplex || null },
      observedAt: new Date().toISOString(), source: 'ssh',
    });
  } catch { throw new OrbiError('INVALID_TELEMETRY', 'Router telemetry was incomplete, malformed or from an unsupported platform. No healthy status was inferred.'); }
}

export function sshArgs(config: RouterConfig): string[] {
  const c = parseConfig(config);
  const quotedHosts = '"' + c.knownHostsFile.replaceAll('\\', '\\\\').replaceAll('"', '\\"').replaceAll('%', '%%') + '"';
  return ['-F', '/dev/null', '-i', c.identityFile, '-p', '22',
    '-o', 'IdentitiesOnly=yes', '-o', 'IdentityAgent=none', '-o', 'BatchMode=yes',
    '-o', 'PasswordAuthentication=no', '-o', 'KbdInteractiveAuthentication=no',
    '-o', 'StrictHostKeyChecking=yes', '-o', `UserKnownHostsFile=${quotedHosts}`,
    '-o', 'GlobalKnownHostsFile=/dev/null', '-o', 'UpdateHostKeys=no', '-o', `HostKeyAlias=${c.hostKeyAlias}`,
    '-o', 'HostKeyAlgorithms=+ssh-rsa', '-o', 'PubkeyAcceptedAlgorithms=+ssh-rsa',
    '-o', 'ConnectTimeout=5', '-o', 'ConnectionAttempts=1', '-o', 'LogLevel=ERROR',
    '-T', `root@${c.host}`, 'sh -s'];
}

export async function getRouterStatus(config: RouterConfig, runner: Runner = run): Promise<RouterStatus> {
  const args = sshArgs(config);
  let result;
  try { result = await runner('ssh', args, READ_STATUS); }
  catch (error) {
    const e = error as { stderr?: string; code?: string; killed?: boolean };
    const stderr = e.stderr || '';
    if (/HOST IDENTIFICATION HAS CHANGED|Host key verification failed|No .*host key is known/i.test(stderr)) {
      throw new OrbiError('HOST_KEY_MISMATCH', 'SSH server identity is unknown or changed. Verify the router identity before updating its trusted key.');
    }
    if (/Permission denied|Load key|invalid format/i.test(stderr)) {
      throw new OrbiError('SSH_AUTH_FAILED', 'SSH key authentication failed. Check the selected identity with orbi-mcp doctor; no enrollment was attempted.');
    }
    if (e.code === 'ENOENT') throw new OrbiError('SSH_MISSING', 'OpenSSH client is not installed or not on PATH.');
    throw new OrbiError('SSH_UNAVAILABLE', 'Could not read router status over SSH. Check the LAN address and SSH availability; no recovery or enrollment was attempted.');
  }
  return parseStatus(result.stdout);
}
