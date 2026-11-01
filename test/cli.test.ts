import test from 'node:test';
import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { mkdtemp, rm } from 'node:fs/promises';
import { testTempRoot as tmpdir } from './fixtures.js';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const cli = fileURLToPath(new URL('../src/cli.js', import.meta.url));
const exec = promisify(execFile);

test('CLI help explains commands without needing router configuration', async () => {
  const result = await exec(process.execPath, [cli, '--help']);
  assert.match(result.stdout, /setup/); assert.match(result.stdout, /doctor/); assert.match(result.stdout, /serve/);
  assert.equal(result.stderr, '');
});

test('doctor returns actionable structured failure and nonzero exit for missing setup', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'orbi-cli-'));
  try {
    await assert.rejects(exec(process.execPath, [cli, 'doctor', '--config', join(dir, 'absent.json')]), (error: unknown) => {
      const e = error as { stdout: string; stderr: string; code: number };
      assert.equal(e.code, 1);
      const report = JSON.parse(e.stdout);
      assert.equal(report.ready, false);
      assert.equal(report.error.code, 'SETUP_REQUIRED');
      assert.equal(report.rebootPersistence, 'not_validated');
      assert.equal(e.stderr, '');
      return true;
    });
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('real stdio server starts without setup, lists tools and reports setup-required on invocation', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'orbi-stdio-'));
  const transport = new StdioClientTransport({ command: process.execPath, args: [cli, 'serve', '--config', join(dir, 'absent.json')], stderr: 'pipe' });
  const client = new Client({ name: 'orbi-stdio-test', version: '1.0.0' });
  let stderr = '';
  transport.stderr?.on('data', chunk => { stderr += chunk.toString(); });
  try {
    await client.connect(transport);
    const tools = await client.listTools();
    assert.equal(tools.tools.length, 1);
    const result = await client.callTool({ name: 'get_router_status', arguments: {} });
    assert.equal(result.isError, true);
    assert.match(JSON.stringify(result), /SETUP_REQUIRED/);
    assert.equal(stderr, '');
  } finally { await client.close(); await rm(dir, { recursive: true, force: true }); }
});
