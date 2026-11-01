import { randomUUID } from 'node:crypto';
import { chmod, mkdir, readFile, realpath, rename, rm, stat, writeFile } from 'node:fs/promises';
import { isIP } from 'node:net';
import { homedir } from 'node:os';
import { basename, dirname, isAbsolute, join, resolve } from 'node:path';
import { z } from 'zod';

export class OrbiError extends Error {
  constructor(public readonly code: string, message: string) { super(message); this.name = 'OrbiError'; }
}

export function validateHost(host: string): string {
  const [address = '', zone, extra] = host.split('%');
  const family = isIP(address);
  let local = false;
  if (family === 4 && !zone) {
    const [a, b] = address.split('.').map(Number);
    local = a === 10 || a === 127 || (a === 172 && b! >= 16 && b! <= 31) || (a === 192 && b === 168);
  } else if (family === 6) {
    const first = Number.parseInt(address.split(':')[0] || '0', 16);
    const linkLocal = (first & 0xffc0) === 0xfe80;
    local = linkLocal || (first & 0xfe00) === 0xfc00 || address === '::1';
    if (zone && (!linkLocal || !/^[a-zA-Z0-9_.-]{1,32}$/.test(zone))) local = false;
  }
  if (!local || extra !== undefined || (host.includes('%') && !zone)) {
    throw new OrbiError('INVALID_HOST', 'Use a literal private LAN IP address (IPv6 link-local may include %interface).');
  }
  return host;
}

const pathSchema = z.string().refine(value => isAbsolute(value) && !/[\x00-\x1f\x7f]/.test(value), 'Expected an absolute file path');
export const configSchema = z.strictObject({
  version: z.literal(1),
  host: z.string().transform(validateHost),
  identityFile: pathSchema,
  knownHostsFile: pathSchema,
  hostKeyAlias: z.string().regex(/^[a-zA-Z0-9_.:-]{1,128}$/),
});
export type RouterConfig = z.infer<typeof configSchema>;
export const parseConfig = (data: unknown): RouterConfig => configSchema.parse(data);
export const defaultConfigPath = (): string => join(process.env.XDG_CONFIG_HOME || join(homedir(), '.config'), 'orbi-mcp', 'config.json');

export async function loadConfig(path: string): Promise<RouterConfig> {
  try { return parseConfig(JSON.parse(await readFile(path, 'utf8'))); }
  catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new OrbiError('SETUP_REQUIRED', 'Router access is not configured. Run orbi-mcp setup in your terminal.');
    }
    throw new OrbiError('INVALID_CONFIG', 'Could not read valid connection settings. Run orbi-mcp setup.');
  }
}

export async function assertSafePaths(path: string, config: RouterConfig): Promise<void> {
  const names = [path, config.identityFile, config.identityFile + '.pub', config.knownHostsFile, path + '.enrollment-pending.json'];
  async function canonical(file: string): Promise<string> {
    try { return await realpath(file); }
    catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
      const parent = dirname(file);
      return parent === file ? file : join(await canonical(parent), basename(file));
    }
  }
  const paths = await Promise.all(names.map(file => canonical(resolve(file))));
  const inodes = await Promise.all(names.map(async file => {
    try { const value = await stat(file); return `${value.dev}:${value.ino}`; }
    catch (error) { if ((error as NodeJS.ErrnoException).code === 'ENOENT') return undefined; throw error; }
  }));
  for (let i = 0; i < names.length; i++) for (let j = i + 1; j < names.length; j++) {
    if (paths[i] === paths[j] || inodes[i] !== undefined && inodes[i] === inodes[j]) {
      throw new OrbiError('CONFIG_PATH_COLLISION', 'Refusing to overwrite an SSH file or enrollment state: output paths collide.');
    }
  }
}

export async function saveConfig(path: string, data: RouterConfig): Promise<void> {
  const config = parseConfig(data);
  await assertSafePaths(path, config);
  await mkdir(dirname(path), { recursive: true, mode: 0o700 });
  const temporary = `${path}.${randomUUID()}.tmp`;
  try {
    await writeFile(temporary, JSON.stringify(config, null, 2) + '\n', { mode: 0o600, flag: 'wx' });
    await chmod(temporary, 0o600);
    await rename(temporary, path);
  } finally { await rm(temporary, { force: true }); }
}

export function publicError(error: unknown): { code: string; message: string } {
  if (error instanceof OrbiError) return { code: error.code, message: error.message };
  return { code: 'OPERATION_FAILED', message: 'Operation failed. Run orbi-mcp doctor for connection checks.' };
}
