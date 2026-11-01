import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { createServer } from 'node:https';
import { testTempRoot as tmpdir } from './fixtures.js';
import { join } from 'node:path';
import type { AddressInfo } from 'node:net';

import { syntheticRsa } from './fixtures.js';

test('password encoding remains one literal shell word, including quotes and shell syntax', async () => {
  const { enrollmentPayload } = await import('../src/enrollment.js');
  for (const password of ['with spaces', "one'quote", '$(echo executed); echo bad', 'back`tick', 'normal']) {
    const payload = JSON.parse(enrollmentPayload(password, syntheticRsa()));
    const observed = execFileSync('/bin/sh', ['-c', `printf '%s' ${payload.password}`], { encoding: 'utf8' });
    assert.equal(observed, password);
  }
  for (const password of ['', '-n', '-ne', 'nul\0byte']) assert.throws(() => enrollmentPayload(password, syntheticRsa()));
});

test('RSA keys reject shell comments, multiple keys and undersized/malformed blobs', async () => {
  const { validateRsaKey } = await import('../src/enrollment.js');
  assert.equal(validateRsaKey(syntheticRsa() + ' harmless-comment'), syntheticRsa());
  for (const value of ["ssh-rsa AAAA bad'quote", syntheticRsa() + '\n' + syntheticRsa(), 'ssh-ed25519 AAAA', 'ssh-rsa AAAA']) assert.throws(() => validateRsaKey(value));
});

test('unsupported firmware stops enrollment before a modifying request', async () => {
  const { inspectTarget, enrollOnce } = await import('../src/enrollment.js');
  const requests: string[] = [];
  const transport = async (method: 'GET' | 'POST', path: string) => {
    requests.push(method + ' ' + path);
    return { status: 200, body: 'Model=RBR850\nFirmware=UNTESTED\n' };
  };
  await assert.rejects(inspectTarget(transport), /firmware|supported/i);
  await assert.rejects(enrollOnce(transport, 'example', syntheticRsa()), /firmware|supported/i);
  assert.ok(requests.every(value => value.startsWith('GET ')));
});

test('enrollment sends one POST and never retries failures', async () => {
  const { enrollOnce } = await import('../src/enrollment.js');
  let posts = 0;
  const transport = async (method: 'GET' | 'POST', path: string) => {
    if (method === 'POST') { posts++; return { status: 403, body: 'private server details' }; }
    return { status: 200, body: path === '/currentsetting.htm' ? 'Model=RBR850\nFirmware=V7.2.8.8_5.1.24\n' : '{"seal_version":"v2.2.9.6-0-gc6614a48"}' };
  };
  await assert.rejects(enrollOnce(transport, 'example', syntheticRsa()), (error: unknown) => {
    assert.ok(error instanceof Error);
    assert.match(error.message, /no automatic retry/i);
    assert.doesNotMatch(error.message, /private server details|example/);
    return true;
  });
  assert.equal(posts, 1);
});

test('TLS pin is checked before any credential-bearing HTTP request reaches the server', async () => {
  const { pinnedRequest, readTlsFingerprint } = await import('../src/enrollment.js');
  const directory = await mkdtemp(join(tmpdir(), 'orbi-tls-'));
  let server: ReturnType<typeof createServer> | undefined;
  try {
    execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1', '-subj', '/CN=localhost', '-keyout', join(directory, 'key.pem'), '-out', join(directory, 'cert.pem')], { stdio: 'ignore' });
    let requests = 0;
    server = createServer({ key: await readFile(join(directory, 'key.pem')), cert: await readFile(join(directory, 'cert.pem')) }, (req, res) => {
      requests++; let body = ''; req.on('data', chunk => { body += chunk; });
      req.on('end', () => { res.writeHead(200); res.end(body || 'OK'); });
    });
    await new Promise<void>(resolve => server!.listen(0, '127.0.0.1', resolve));
    const port = (server.address() as AddressInfo).port;
    const pin = await readTlsFingerprint('127.0.0.1', port);
    assert.match(pin, /^[a-f0-9]{64}$/);
    await assert.rejects(pinnedRequest('127.0.0.1', createHash('sha256').update('wrong').digest('hex'), 'POST', '/api/v1/enable_ssh', 'synthetic-password', port), /certificate|identity/i);
    assert.equal(requests, 0);
    const result = await pinnedRequest('127.0.0.1', pin, 'POST', '/api/v1/enable_ssh', 'synthetic-password', port);
    assert.equal(result.body, 'synthetic-password');
    assert.equal(requests, 1);
  } finally {
    if (server) { server.closeAllConnections(); await new Promise<void>(resolve => server!.close(() => resolve())); }
    await rm(directory, { recursive: true, force: true });
  }
});

test('untested SeAL suffixes and echo backslash inputs are refused', async () => {
  const { inspectTarget, enrollmentPayload } = await import('../src/enrollment.js');
  const transport = async (_method: 'GET' | 'POST', path: string) => ({ status: 200, body: path === '/currentsetting.htm' ? 'Model=RBR850\nFirmware=V7.2.8.8_5.1.24\n' : '{"seal_version":"v2.2.9.6-untested"}' });
  await assert.rejects(inspectTarget(transport), /SeAL/i);
  for (const value of ['back\\slash', 'line\\nend', 'stop\\cend']) assert.throws(() => enrollmentPayload(value, syntheticRsa()), /password/i);
});
