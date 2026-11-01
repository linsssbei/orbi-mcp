import test from 'node:test';
import assert from 'node:assert/strict';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { nativeStatus } from './fixtures.js';
import { parseStatus } from '../src/router.js';

async function connected(loader: () => Promise<ReturnType<typeof parseStatus>>) {
  const { createServer } = await import('../src/server.js');
  const server = createServer(loader);
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  const client = new Client({ name: 'orbi-test', version: '1.0.0' });
  await server.connect(serverTransport);
  await client.connect(clientTransport);
  return { client, server };
}

test('MCP advertises exactly one typed read-only tool and returns structured native status', async () => {
  let calls = 0;
  const { client, server } = await connected(async () => { calls++; return parseStatus(nativeStatus); });
  try {
    const list = await client.listTools();
    assert.deepEqual(list.tools.map(tool => tool.name), ['get_router_status']);
    assert.equal(list.tools[0]!.annotations?.readOnlyHint, true);
    assert.equal(list.tools[0]!.annotations?.destructiveHint, false);
    assert.ok(list.tools[0]!.outputSchema);
    assert.equal(calls, 0);
    const result = await client.callTool({ name: 'get_router_status', arguments: {} });
    assert.equal(result.isError, undefined);
    const data = result.structuredContent as Record<string, unknown>;
    assert.equal(data.model, 'RBR850');
    assert.equal((data.memory as { totalBytes: number }).totalBytes, 819200000);
    assert.equal(calls, 1);
  } finally { await client.close(); await server.close(); }
});

test('MCP failures omit raw exceptions and never turn missing access into successful telemetry', async () => {
  const { client, server } = await connected(async () => { throw new Error('synthetic-password and private router response'); });
  try {
    const result = await client.callTool({ name: 'get_router_status', arguments: {} });
    assert.equal(result.isError, true);
    assert.equal(result.structuredContent, undefined);
    const text = JSON.stringify(result);
    assert.doesNotMatch(text, /synthetic-password|private router response/);
    assert.match(text, /doctor/);
  } finally { await client.close(); await server.close(); }
});

test('MCP rejects unknown arguments instead of accepting arbitrary commands', async () => {
  let calls = 0;
  const { client, server } = await connected(async () => { calls++; return parseStatus(nativeStatus); });
  try {
    const result = await client.callTool({ name: 'get_router_status', arguments: { command: 'reboot' } });
    assert.equal(result.isError, true);
    assert.equal(calls, 0);
  } finally { await client.close(); await server.close(); }
});
