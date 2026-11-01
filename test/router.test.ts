import test from 'node:test';
import assert from 'node:assert/strict';
import { configAt, nativeStatus } from './fixtures.js';

test('native status parser reports real units rather than SOAP memory guesses', async () => {
  const { parseStatus } = await import('../src/router.js');
  const data = parseStatus(nativeStatus);
  assert.equal(data.model, 'RBR850');
  assert.equal(data.firmware, 'V7.2.8.8_5.1.24');
  assert.equal(data.uptimeSeconds, 12345.5);
  assert.deepEqual(data.loadAverage, { oneMinute: 0.25, fiveMinutes: 0.5, fifteenMinutes: 0.75 });
  assert.deepEqual(data.memory, { totalBytes: 819200000, availableBytes: 409600000 });
  assert.deepEqual(data.wan, { interface: 'eth4', linkUp: true, speedMbps: 2500, duplex: 'full' });
  assert.equal(data.source, 'ssh');
  assert.ok(Number.isFinite(Date.parse(data.observedAt)));
});

test('missing or corrupted telemetry fails rather than becoming healthy zeroes', async () => {
  const { parseStatus } = await import('../src/router.js');
  for (const bad of ['', nativeStatus.replace('12345.50', 'garbage'), nativeStatus.replace('MemAvailable:', 'Missing:'), nativeStatus.replace('Link detected: yes', 'Link detected: unknown')]) {
    assert.throws(() => parseStatus(bad), /telemetry/i);
  }
  const down = parseStatus(nativeStatus.replace('2500Mb/s', 'Unknown!').replace('Duplex: Full', 'Duplex: Unknown!').replace('Link detected: yes', 'Link detected: no'));
  assert.deepEqual(down.wan, { interface: 'eth4', linkUp: false, speedMbps: null, duplex: null });
});

test('SSH collector pins identity, restricts commands and never embeds user fields in its script', async () => {
  const { getRouterStatus } = await import('../src/router.js');
  let invocation: { file: string; args: string[]; input: string | undefined } | undefined;
  const status = await getRouterStatus(configAt('/tmp/orbi-test'), async (file, args, input) => {
    invocation = { file, args, input };
    return { stdout: nativeStatus, stderr: '' };
  });
  assert.equal(status.model, 'RBR850');
  assert.equal(invocation?.file, 'ssh');
  assert.ok(invocation?.args.includes('StrictHostKeyChecking=yes'));
  assert.ok(invocation?.args.includes('BatchMode=yes'));
  assert.ok(invocation?.args.includes('PasswordAuthentication=no'));
  assert.ok(invocation?.args.includes('HostKeyAlias=orbi-mcp-router'));
  assert.equal(invocation?.args.at(-1), 'sh -s');
  assert.ok(invocation?.input?.includes('cat /proc/meminfo'));
  assert.ok(!invocation?.input?.includes('192.168.1.1'));
});

test('SSH errors are actionable and do not echo subprocess output', async () => {
  const { getRouterStatus } = await import('../src/router.js');
  await assert.rejects(getRouterStatus(configAt('/tmp/orbi-test'), async () => {
    throw Object.assign(new Error('secret fixture'), { stderr: 'Permission denied (publickey). secret fixture' });
  }), (error: unknown) => {
    assert.ok(error instanceof Error);
    assert.match(error.message, /key|authentication/i);
    assert.doesNotMatch(error.message, /secret fixture/);
    return true;
  });
});

test('contradictory or duplicate port telemetry cannot report a healthy link', async () => {
  const { parseStatus } = await import('../src/router.js');
  for (const line of ['Link detected: no', 'Link detected: yes', 'Speed: 100Mb/s', 'Duplex: Half']) {
    assert.throws(() => parseStatus(nativeStatus + line + '\n'), /telemetry/i);
    assert.throws(() => parseStatus(nativeStatus.replace('Settings for eth4:', 'Settings for eth4:\n' + line)), /telemetry/i);
  }
});
