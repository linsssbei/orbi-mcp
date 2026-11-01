import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { createServer } from 'node:https';
import type { AddressInfo } from 'node:net';
import { join } from 'node:path';
import { nativeStatus, syntheticRsa, testTempRoot } from './fixtures.js';
import { parseStatus } from '../src/router.js';
import { run } from '../src/process.js';
import type { SetupDependencies } from '../src/setup.js';
import type { Prompts } from '../src/prompt.js';

async function withRouter(check: (context: {
  dir: string; configPath: string; deps: SetupDependencies;
  state: { posts: number; received?: Record<string, string>; disconnectOnPost: boolean };
}) => Promise<void>): Promise<void> {
  const dir = await mkdtemp(join(testTempRoot(), 'orbi-wizard-'));
  let server: ReturnType<typeof createServer> | undefined;
  try {
    execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=localhost', '-keyout', join(dir, 'tls.key'), '-out', join(dir, 'tls.pem')], { stdio: 'ignore' });
    const state: { posts: number; received?: Record<string, string>; disconnectOnPost: boolean } = { posts: 0, disconnectOnPost: false };
    server = createServer({ key: await readFile(join(dir, 'tls.key')), cert: await readFile(join(dir, 'tls.pem')) }, (req, res) => {
      if (req.method === 'POST') {
        state.posts++; let body = '';
        req.on('data', chunk => { body += chunk; });
        req.on('end', () => {
          state.received = JSON.parse(body);
          if (state.disconnectOnPost) res.destroy(); else res.end('OK');
        });
      } else res.end(req.url === '/currentsetting.htm' ? 'Model=RBR850\nFirmware=V7.2.8.8_5.1.24\n' : '{"seal_version":"v2.2.9.6-0-gc6614a48"}');
    });
    await new Promise<void>(resolve => server!.listen(0, '127.0.0.1', resolve));
    const deps: SetupDependencies = {
      httpsPort: (server.address() as AddressInfo).port,
      probe: async () => state.posts && !state.disconnectOnPost ? 'SSH-2.0-dropbear_2019.78' : null,
      getStatus: async () => parseStatus(nativeStatus),
      runner: async (file, args, input) => file === 'ssh-keyscan' ? { stdout: `127.0.0.1 ${syntheticRsa()}\n`, stderr: '' } : run(file, args, input),
    };
    await check({ dir, configPath: join(dir, 'settings', 'config.json'), deps, state });
  } finally {
    if (server) { server.closeAllConnections(); await new Promise<void>(resolve => server!.close(() => resolve())); }
    await rm(dir, { recursive: true, force: true });
  }
}

function scriptedPrompts(): { prompts: Prompts; log: string[]; answers: string[]; hidden: { used: boolean } } {
  const answers = ['yes', 'enable', "synthetic'password", 'yes'];
  const log: string[] = []; const hidden = { used: false };
  return { answers, log, hidden, prompts: {
    log: message => { log.push(message); },
    ask: async (message, secret) => { log.push(message); if (secret) hidden.used = true; return answers.shift()!; },
  } };
}

test('guided setup enrolls once, hides the password and verifies key-only SSH before saving', async () => {
  const { setup } = await import('../src/setup.js');
  const { loadConfig } = await import('../src/config.js');
  await withRouter(async ({ configPath, deps, state }) => {
    const p = scriptedPrompts();
    await setup({ configPath, host: '127.0.0.1' }, p.prompts, deps);
    assert.equal(state.posts, 1); assert.equal(state.received?.username, 'admin');
    assert.ok(p.hidden.used); assert.doesNotMatch(p.log.join('\n'), /synthetic'password/);
    const config = await loadConfig(configPath);
    assert.match(await readFile(config.knownHostsFile, 'utf8'), /^orbi-mcp-router ssh-rsa /);
    assert.equal((await stat(config.identityFile)).mode & 0o777, 0o600);
    assert.ok(!JSON.stringify(config).includes('password')); assert.equal(p.answers.length, 0);
    await assert.rejects(stat(configPath + '.enrollment-pending.json'), /ENOENT/);
  });
});

test('a lost enrollment response leaves a marker that prevents a second modifying attempt', async () => {
  const { setup } = await import('../src/setup.js');
  await withRouter(async ({ configPath, deps, state }) => {
    state.disconnectOnPost = true;
    await assert.rejects(setup({ configPath, host: '127.0.0.1' }, scriptedPrompts().prompts, deps), /request failed/i);
    const second = scriptedPrompts();
    await assert.rejects(setup({ configPath, host: '127.0.0.1' }, second.prompts, deps), /pending|uncertain/i);
    assert.equal(state.posts, 1);
    const marker = configPath + '.enrollment-pending.json';
    assert.equal((await stat(marker)).mode & 0o777, 0o600);
    assert.doesNotMatch(await readFile(marker, 'utf8'), /synthetic'password/);
    assert.equal(second.hidden.used, false);
  });
});

test('a stale public-key file never replaces router authorization or prompts for a password', async () => {
  const { setup, generateIdentity } = await import('../src/setup.js');
  await withRouter(async ({ dir, configPath, deps, state }) => {
    const identity = join(dir, 'settings', 'id_rsa'); const other = join(dir, 'other');
    await generateIdentity(identity); await generateIdentity(other);
    await writeFile(identity + '.pub', await readFile(other + '.pub'));
    const p = scriptedPrompts();
    await assert.rejects(setup({ configPath, host: '127.0.0.1' }, p.prompts, deps), /match|pair/i);
    assert.equal(state.posts, 0); assert.equal(p.hidden.used, false);
  });
});
