import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm, stat } from 'node:fs/promises';
import { testTempRoot as tmpdir } from './fixtures.js';
import { join } from 'node:path';
import { configAt } from './fixtures.js';

test('private configuration round trips without key or password contents', async () => {
  const { saveConfig, loadConfig } = await import('../src/config.js');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-config-'));
  try {
    const path = join(dir, 'settings', 'config.json');
    const config = configAt(dir);
    await saveConfig(path, config);
    assert.deepEqual(await loadConfig(path), config);
    assert.equal((await stat(path)).mode & 0o777, 0o600);
    assert.equal((await stat(join(dir, 'settings'))).mode & 0o777, 0o700);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('configuration rejects shell/options injection and public targets', async () => {
  const { parseConfig, validateHost } = await import('../src/config.js');
  const config = configAt('/tmp/orbi-example');
  for (const host of ['-oProxyCommand=bad', '192.168.1.1;id', 'example.com', '8.8.8.8', '::ffff:8.8.8.8', 'fe80::1%en0;id']) {
    assert.throws(() => validateHost(host), /LAN|address|host/i);
  }
  assert.equal(validateHost('fe80::1%en0'), 'fe80::1%en0');
  assert.equal(validateHost('192.168.1.1'), '192.168.1.1');
  assert.throws(() => parseConfig({ ...config, hostKeyAlias: 'x -oProxyCommand=y' }));
  assert.throws(() => parseConfig({ ...config, identityFile: 'relative/key' }));
  assert.throws(() => parseConfig({ ...config, password: 'must-not-persist' }));
});

test('saving connection settings cannot overwrite either referenced SSH file', async () => {
  const { saveConfig } = await import('../src/config.js');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-config-'));
  try {
    const config = configAt(dir);
    for (const target of [config.identityFile, config.knownHostsFile]) {
      await assert.rejects(saveConfig(target, config), /overwrite|SSH file/i);
    }
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('settings cannot overwrite a public key, including through a directory symlink', async () => {
  const { saveConfig } = await import('../src/config.js');
  const { symlink } = await import('node:fs/promises');
  const dir = await mkdtemp(join(tmpdir(), 'orbi-alias-'));
  try {
    const config = configAt(dir);
    await assert.rejects(saveConfig(config.identityFile + '.pub', config), /overwrite|colli|SSH file/i);
    const alias = join(dir, 'alias');
    await symlink(dir, alias);
    await assert.rejects(saveConfig(join(alias, 'id_rsa.pub'), config), /overwrite|colli|SSH file/i);
  } finally { await rm(dir, { recursive: true, force: true }); }
});
