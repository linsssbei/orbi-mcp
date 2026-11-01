import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { testTempRoot as tmpdir } from './fixtures.js';
import { join } from 'node:path';
import { configAt, nativeStatus } from './fixtures.js';
import { parseStatus } from '../src/router.js';

const noPrompt = { ask: async (): Promise<string> => { throw new Error('unexpected prompt'); }, log: (_message: string): void => {} };

test('setup reuses explicitly trusted SSH without enrollment or private-key copying', async () => {
  const { setup } = await import('../src/setup.js');
  const { loadConfig } = await import('../src/config.js');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-setup-'));
  try {
    const config = configAt(dir);
    await writeFile(config.identityFile, 'synthetic-private-key', { mode: 0o600 });
    await writeFile(config.knownHostsFile, 'synthetic trusted key', { mode: 0o600 });
    const configPath = join(dir, 'settings', 'config.json');
    await setup({ configPath, host: config.host, identityFile: config.identityFile, knownHostsFile: config.knownHostsFile, hostKeyAlias: config.hostKeyAlias, nonInteractive: true }, noPrompt, {
      getStatus: async () => parseStatus(nativeStatus),
      probe: async () => { throw new Error('unexpected network enrollment preflight'); },
    });
    assert.deepEqual(await loadConfig(configPath), config);
    assert.equal(await readFile(config.identityFile, 'utf8'), 'synthetic-private-key');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('noninteractive setup never enrolls, asks for secrets or generates keys', async () => {
  const { setup } = await import('../src/setup.js');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-setup-'));
  try {
    await assert.rejects(setup({ configPath: join(dir, 'config.json'), host: '192.168.1.1', nonInteractive: true }, noPrompt), /interactive|existing|setup/i);
    await assert.rejects(readFile(join(dir, 'id_rsa')), /ENOENT/);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('occupied SSH port never triggers enrollment or key replacement', async () => {
  const { setup } = await import('../src/setup.js');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-setup-'));
  try {
    await assert.rejects(setup({ configPath: join(dir, 'config.json'), host: '192.168.1.1' }, noPrompt, { probe: async () => 'SSH-2.0-OpenSSH_vendor' }), /occupied|existing SSH/i);
    await assert.rejects(readFile(join(dir, 'id_rsa')), /ENOENT/);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('identity generation refuses to overwrite an existing key', async () => {
  const { generateIdentity } = await import('../src/setup.js');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-key-'));
  try {
    const path = join(dir, 'id_rsa');
    await writeFile(path, 'keep this key', { mode: 0o600 });
    await assert.rejects(generateIdentity(path), /exist|overwrite/i);
    assert.equal(await readFile(path, 'utf8'), 'keep this key');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('pending enrollment blocks another setup attempt before network access', async () => {
  const { setup } = await import('../src/setup.js');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-pending-'));
  try {
    const path = join(dir, 'config.json');
    await writeFile(path + '.enrollment-pending.json', JSON.stringify({ host: '127.0.0.1', identityFile: join(dir, 'id_rsa') }), { mode: 0o600 });
    let probes = 0;
    await assert.rejects(setup({ configPath: path, host: '127.0.0.1' }, noPrompt, { probe: async () => { probes++; throw new Error('unexpected repeated preflight'); } }), /pending|uncertain/i);
    assert.equal(probes, 0);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('setup rejects a future public-key/config path collision before network access', async () => {
  const { setup } = await import('../src/setup.js');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-collision-'));
  try {
    let probes = 0;
    await assert.rejects(setup({ configPath: join(dir, 'id_rsa.pub'), identityFile: join(dir, 'id_rsa'), host: '127.0.0.1' }, noPrompt, { probe: async () => { probes++; throw new Error('unexpected preflight'); } }), /overwrite|colli|SSH file/i);
    assert.equal(probes, 0);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('private/public key mismatch is detected before enrollment', async () => {
  const { generateIdentity, verifyIdentity } = await import('../src/setup.js');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-keypair-'));
  try {
    const key = join(dir, 'key'); const other = join(dir, 'other');
    await generateIdentity(key); await generateIdentity(other);
    await writeFile(key + '.pub', await readFile(other + '.pub'));
    await assert.rejects(verifyIdentity(key), /match|pair/i);
  } finally { await rm(dir, { recursive: true, force: true }); }
});
