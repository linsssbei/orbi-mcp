#!/usr/bin/env node
import { resolve } from 'node:path';
import { parseArgs } from 'node:util';
import { defaultConfigPath, OrbiError, publicError } from './config.js';
import { doctor } from './doctor.js';
import { serve, VERSION } from './server.js';
import { setup, type SetupOptions } from './setup.js';

const HELP = `Usage: orbi-mcp <setup|doctor|serve> [options]

  setup       Guided SSH setup, or reuse an existing authorized key
  doctor      Read-only configuration, SSH and telemetry checks; JSON output
  serve       Start the read-only MCP server over stdio

Options:
  --config PATH          Connection settings (default: ~/.config/orbi-mcp/config.json)
  --help                 Show this help
  --version              Show version

Setup options:
  --host IP              Router private LAN IP; IPv6 may include %interface
  --identity PATH        Existing SSH private key (not copied or overwritten)
  --known-hosts PATH     Existing trusted known-hosts file
  --host-key-alias NAME  Entry name in known-hosts (default: orbi-mcp-router)
  --non-interactive      Reuse existing trusted access only; never enroll

Reboot persistence is not validated. No startup repair is performed.
`;

async function main(): Promise<void> {
  let parsed: ReturnType<typeof parseArgs>;
  try {
    parsed = parseArgs({ allowPositionals: true, strict: true, options: {
      config: { type: 'string' }, host: { type: 'string' }, identity: { type: 'string' },
      'known-hosts': { type: 'string' }, 'host-key-alias': { type: 'string' },
      'non-interactive': { type: 'boolean' }, help: { type: 'boolean' }, version: { type: 'boolean' },
    } });
  } catch { throw new OrbiError('INVALID_ARGUMENTS', 'Invalid command arguments. Run orbi-mcp --help. Never pass passwords as arguments.'); }
  const { values, positionals } = parsed;
  if (values.help || !positionals.length && !values.version) { process.stdout.write(HELP); return; }
  if (values.version) { process.stdout.write(VERSION + '\n'); return; }
  const command = positionals[0];
  if (positionals.length !== 1 || !['setup', 'doctor', 'serve'].includes(command!)) throw new OrbiError('INVALID_ARGUMENTS', 'Choose setup, doctor or serve. Run orbi-mcp --help.');
  if (command !== 'setup' && ['host', 'identity', 'known-hosts', 'host-key-alias', 'non-interactive'].some(key => values[key] !== undefined)) {
    throw new OrbiError('INVALID_ARGUMENTS', 'Connection options belong to setup. Doctor and serve read saved settings.');
  }
  const path = resolve(typeof values.config === 'string' ? values.config : defaultConfigPath());
  if (command === 'setup') {
    const options: SetupOptions = { configPath: path };
    if (typeof values.host === 'string') options.host = values.host;
    if (typeof values.identity === 'string') options.identityFile = resolve(values.identity);
    if (typeof values['known-hosts'] === 'string') options.knownHostsFile = resolve(values['known-hosts']);
    if (typeof values['host-key-alias'] === 'string') options.hostKeyAlias = values['host-key-alias'];
    if (values['non-interactive']) options.nonInteractive = true;
    await setup(options);
    process.stderr.write('MCP client entry (replace command with your node executable if needed):\n');
    process.stderr.write(JSON.stringify({ mcpServers: { orbi: { command: process.execPath, args: [resolve(process.argv[1]!), 'serve', '--config', path] } } }, null, 2) + '\n');
  } else if (command === 'doctor') {
    const result = await doctor(path);
    process.stdout.write(JSON.stringify(result, null, 2) + '\n');
    if (!result.ready) process.exitCode = 1;
  } else await serve(path);
}

main().catch(error => {
  const failure = publicError(error);
  process.stderr.write(`${failure.code}: ${failure.message}\n`);
  process.exitCode = 1;
});
