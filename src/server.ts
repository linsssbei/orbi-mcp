import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { loadConfig, publicError } from './config.js';
import { getRouterStatus, statusSchema, type RouterStatus } from './router.js';
import { checkConnectionFiles } from './setup.js';

export const VERSION = '0.1.0';

export function createServer(loadStatus: () => Promise<RouterStatus>): McpServer {
  const server = new McpServer({ name: 'orbi-mcp', version: VERSION });
  server.registerTool('get_router_status', {
    title: 'Read Orbi router status',
    description: 'Read model, firmware, uptime, CPU load averages, memory bytes and physical WAN link telemetry over pinned-key SSH. Does not change settings, reboot, enable SSH or run arbitrary commands. WAN link-up does not establish Internet reachability.',
    inputSchema: z.strictObject({}),
    outputSchema: statusSchema,
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false },
  }, async () => {
    try {
      const snapshot = statusSchema.parse(await loadStatus());
      return { content: [{ type: 'text' as const, text: JSON.stringify(snapshot) }], structuredContent: { ...snapshot } };
    } catch (error) {
      return { isError: true, content: [{ type: 'text' as const, text: JSON.stringify(publicError(error)) }] };
    }
  });
  return server;
}

export async function serve(configPath: string): Promise<void> {
  const server = createServer(async () => {
    const config = await loadConfig(configPath);
    await checkConnectionFiles(config);
    return getRouterStatus(config);
  });
  const stop = (): void => { void server.close().finally(() => process.exit(0)); };
  process.once('SIGINT', stop);
  process.once('SIGTERM', stop);
  await server.connect(new StdioServerTransport());
}
