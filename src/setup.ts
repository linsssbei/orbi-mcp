import { access, chmod, mkdir, open, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { OrbiError, assertSafePaths, loadConfig, parseConfig, saveConfig, validateHost, type RouterConfig } from './config.js';
import { enrollOnce, inspectTarget, keyFingerprint, pinnedRequest, probeSsh, readTlsFingerprint, validateRsaKey } from './enrollment.js';
import { run, type Runner } from './process.js';
import { terminalPrompts, type Prompts } from './prompt.js';
import { getRouterStatus } from './router.js';

export interface SetupOptions {
  configPath: string; host?: string; identityFile?: string; knownHostsFile?: string; hostKeyAlias?: string; nonInteractive?: boolean;
}
export interface SetupDependencies { getStatus?: typeof getRouterStatus; probe?: typeof probeSsh; httpsPort?: number; runner?: Runner }
const exists = async (path: string): Promise<boolean> => { try { await access(path); return true; } catch (e) { if ((e as NodeJS.ErrnoException).code === 'ENOENT') return false; throw e; } };

export async function checkConnectionFiles(config: RouterConfig): Promise<void> {
  const identity = await stat(config.identityFile).catch(() => { throw new OrbiError('IDENTITY_MISSING', 'SSH private key is missing. Supply its path to orbi-mcp setup.'); });
  if (!identity.isFile() || (identity.mode & 0o077)) throw new OrbiError('IDENTITY_PERMISSIONS', 'SSH private key must be a file accessible only by its owner (mode 0600 or 0400).');
  const hosts = await stat(config.knownHostsFile).catch(() => { throw new OrbiError('TRUST_MISSING', 'SSH known-hosts file is missing. Verify server identity through orbi-mcp setup.'); });
  if (!hosts.isFile() || (hosts.mode & 0o022)) throw new OrbiError('TRUST_PERMISSIONS', 'SSH known-hosts file must not be writable by other users.');
}

export async function generateIdentity(path: string): Promise<void> {
  if (await exists(path) || await exists(path + '.pub')) throw new OrbiError('KEY_EXISTS', 'Key file already exists; refusing to overwrite it.');
  await mkdir(dirname(path), { recursive: true, mode: 0o700 });
  await run('ssh-keygen', ['-q', '-t', 'rsa', '-b', '3072', '-N', '', '-C', 'orbi-mcp', '-f', path]);
  await chmod(path, 0o600);
}

export async function verifyIdentity(path: string): Promise<string> {
  try {
    const expected = validateRsaKey(await readFile(path + '.pub', 'utf8'));
    const derived = await run('ssh-keygen', ['-y', '-P', '', '-f', path]);
    if (validateRsaKey(derived.stdout) !== expected) throw new Error('mismatch');
    return expected;
  } catch { throw new OrbiError('KEY_PAIR_MISMATCH', 'Private/public SSH key pair does not match or cannot be read noninteractively. No enrollment was sent.'); }
}

async function trustServer(config: RouterConfig, prompts: Prompts, runner: Runner): Promise<void> {
  if (await exists(config.knownHostsFile)) throw new OrbiError('TRUST_EXISTS', 'Trusted server keys already exist; refusing to replace them automatically.');
  const { stdout } = await runner('ssh-keyscan', ['-T', '5', '-t', 'rsa', config.host]);
  const keys = new Set(stdout.split(/\r?\n/).filter(line => line && !line.startsWith('#')).map(line => validateRsaKey(line.split(/\s+/).slice(1).join(' '))));
  if (keys.size !== 1) throw new OrbiError('HOST_KEY_UNAVAILABLE', 'Could not obtain one unambiguous RSA host key. Verify router identity before retrying setup.');
  const key = [...keys][0]!;
  prompts.log(`SSH server fingerprint: ${keyFingerprint(key)}`);
  if ((await prompts.ask('Verify this router identity and trust this SSH key? Type yes: ')).trim() !== 'yes') throw new OrbiError('SETUP_CANCELLED', 'SSH identity was not trusted.');
  await mkdir(dirname(config.knownHostsFile), { recursive: true, mode: 0o700 });
  await writeFile(config.knownHostsFile, `${config.hostKeyAlias} ${key}\n`, { flag: 'wx', mode: 0o600 });
}

export async function setup(options: SetupOptions, prompts: Prompts = terminalPrompts, deps: SetupDependencies = {}): Promise<RouterConfig> {
  const status = deps.getStatus || getRouterStatus;
  const probe = deps.probe || probeSsh;
  const runner = deps.runner || run;
  const path = resolve(options.configPath);
  let previous: RouterConfig | undefined;
  if (await exists(path)) previous = await loadConfig(path);
  const host = validateHost(options.host || previous?.host || (options.nonInteractive ? '' : (await prompts.ask('Router LAN IP [192.168.1.1]: ')).trim() || '192.168.1.1'));
  const config = parseConfig({ version: 1, host,
    identityFile: resolve(options.identityFile || previous?.identityFile || resolve(dirname(path), 'id_rsa')),
    knownHostsFile: resolve(options.knownHostsFile || previous?.knownHostsFile || resolve(dirname(path), 'known_hosts')),
    hostKeyAlias: options.hostKeyAlias || previous?.hostKeyAlias || 'orbi-mcp-router',
  });
  await assertSafePaths(path, config);
  const pendingPath = path + '.enrollment-pending.json';
  const pending = await exists(pendingPath);
  if (pending) {
    let state: { host?: string; identityFile?: string };
    try { state = JSON.parse(await readFile(pendingPath, 'utf8')); }
    catch { throw new OrbiError('ENROLLMENT_PENDING', 'Pending enrollment state needs inspection. No new enrollment will be sent.'); }
    if (state.host !== host || state.identityFile !== config.identityFile) {
      throw new OrbiError('ENROLLMENT_PENDING', 'Pending enrollment belongs to a different target or key. Inspect the saved state before continuing.');
    }
  }
  if (await exists(config.identityFile) && await exists(config.knownHostsFile)) {
    await checkConnectionFiles(config);
    const snapshot = await status(config);
    await saveConfig(path, config);
    if (pending) await rm(pendingPath);
    prompts.log(`Existing key-only SSH verified: ${snapshot.model} ${snapshot.firmware}. No router changes made.`);
    return config;
  }
  if (pending) throw new OrbiError('ENROLLMENT_PENDING', 'A previous enrollment result is pending or uncertain. Verify existing SSH access and supply its trusted key files; another enrollment will not be sent.');
  if (options.nonInteractive) throw new OrbiError('INTERACTIVE_REQUIRED', 'Noninteractive setup requires an existing private key and trusted known-hosts file; enrollment needs an interactive terminal.');
  if (previous) throw new OrbiError('SETUP_INCOMPLETE', 'Saved SSH access is incomplete. Repair the selected local files; keys will not be replaced or re-enrolled automatically.');
  const banner = await probe(host);
  if (banner !== null) {
    if (!await exists(config.identityFile)) throw new OrbiError('SSH_OCCUPIED', 'TCP 22 is occupied by an existing SSH service. Supply its authorized identity and trusted known-hosts file; enrollment was not sent.');
    await trustServer(config, prompts, runner);
  } else {
    if (await exists(config.knownHostsFile)) throw new OrbiError('SSH_UNAVAILABLE', 'Existing SSH trust is configured but SSH is unavailable. Diagnose connectivity; do not re-enroll automatically.');
    const pin = await readTlsFingerprint(host, deps.httpsPort);
    prompts.log(`Router HTTPS certificate SHA256: ${pin}`);
    prompts.log('This is first-use identity verification. Confirm the LAN target independently before supplying credentials.');
    if ((await prompts.ask('Trust this router HTTPS certificate? Type yes: ')).trim() !== 'yes') throw new OrbiError('SETUP_CANCELLED', 'Router HTTPS identity was not trusted.');
    const transport = (method: 'GET' | 'POST', route: string, body?: string) => pinnedRequest(host, pin, method, route, body, deps.httpsPort);
    await inspectTarget(transport);
    prompts.log('Enrollment replaces Dropbear authorized_keys, regenerates its SSH server key, updates /etc/shells and starts key-only SSH. It does not reboot the router or configure startup.');
    if ((await prompts.ask('Enable SSH with this dedicated key? Type enable: ')).trim() !== 'enable') throw new OrbiError('SETUP_CANCELLED', 'Enrollment cancelled.');
    if (!await exists(config.identityFile)) await generateIdentity(config.identityFile);
    const publicKey = await verifyIdentity(config.identityFile);
    const identity = await stat(config.identityFile);
    if (!identity.isFile() || (identity.mode & 0o077)) throw new OrbiError('IDENTITY_PERMISSIONS', 'Private key must have owner-only permissions before enrollment.');
    let password = await prompts.ask('Router admin password (hidden): ', true);
    try {
      // Check the listener again immediately before the single modifying request.
      if (await probe(host) !== null) throw new OrbiError('SSH_OCCUPIED', 'SSH became available; enrollment was not sent.');
      const marker = await open(pendingPath, 'wx', 0o600);
      try {
        await marker.writeFile(JSON.stringify({ host, identityFile: config.identityFile, keyFingerprint: keyFingerprint(publicKey), certificateSha256: pin, attemptedAt: new Date().toISOString() }) + '\n');
        await marker.sync();
      } finally { await marker.close(); }
      await enrollOnce(transport, password, publicKey);
    } finally { password = ''; }
    const after = await probe(host);
    if (!after || !after.toLowerCase().includes('dropbear')) throw new OrbiError('ENROLLMENT_UNCONFIRMED', 'Dropbear startup was not confirmed. Do not repeat enrollment automatically; inspect SSH availability first.');
    await trustServer(config, prompts, runner);
  }
  await checkConnectionFiles(config);
  const snapshot = await status(config);
  await saveConfig(path, config);
  if (await exists(pendingPath)) await rm(pendingPath);
  prompts.log(`Key-only SSH verified: ${snapshot.model} ${snapshot.firmware}. Settings saved to ${path}.`);
  prompts.log('SSH startup after reboot is not validated. No boot files were modified.');
  return config;
}
