'use strict';

const Netgear = require('netgear');
const { execFileSync, spawnSync } = require('node:child_process');
const { isIP } = require('node:net');
const { writeFileSync, chmodSync } = require('node:fs');
const { join } = require('node:path');

async function main() {
  const command = process.argv[2] || 'discover';
  if (!['auth', 'discover', 'info', 'devices', 'config'].includes(command)) {
    throw new Error('Usage: node router.cjs [auth|discover|info|devices|config]');
  }

  const host = process.env.ORBI_HOST || '192.168.1.1';
  if (isIP(host) !== 4) throw new Error('ORBI_HOST must be an IPv4 address.');
  const keychainService = `local-orbi-tools:${host}`;

  if (command === 'auth') {
    if (!process.stdin.isTTY) throw new Error('Run npm run auth in an interactive terminal.');
    // With -w last and no password argument, security prompts without exposing it in argv.
    const result = spawnSync('/usr/bin/security', [
      'add-generic-password', '-U', '-a', 'admin', '-s', keychainService, '-w',
    ], { stdio: 'inherit' });
    if (result.error || result.status !== 0) throw new Error('Keychain setup did not complete.');
    console.log(`Admin password saved in macOS Keychain for ${host}.`);
    return;
  }

  const router = new Netgear({ host, timeout: 6000, logLevel: 'silent' });
  if (command === 'discover') {
    const settings = await router.getCurrentSetting();
    console.log(JSON.stringify({
      host: settings.host,
      model: settings.Model,
      firmware: settings.Firmware,
      internet: settings.InternetConnectionStatus,
      soapVersion: settings.SOAPVersion,
      loginMethod: settings.LoginMethod,
      port: Number(settings.port),
      tls: settings.tls,
    }, null, 2));
    return;
  }

  let password;
  try {
    // Capture the exact, host-specific Keychain item in memory; never print its output.
    password = execFileSync('/usr/bin/security', [
      'find-generic-password', '-a', 'admin', '-s', keychainService, '-w',
    ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 5000 })
      .replace(/\r?\n$/, '');
  } catch {
    if (!process.stdin.isTTY) {
      throw new Error('No accessible Orbi Keychain login. Run npm run auth once in your terminal.');
    }
    // getpass reads from the terminal without echoing. Its output stays in this process.
    password = execFileSync('python3', ['-c',
      'import getpass; print(getpass.getpass("Orbi admin password: "), end="")',
    ], { encoding: 'utf8', stdio: ['inherit', 'pipe', 'inherit'] });
  }
  if (!password) throw new Error('Password cannot be empty.');

  try {
    if (!await router.login({ password, username: 'admin' })) {
      throw new Error('Router login failed.');
    }
    if (command === 'config') {
      const report = { host, capturedAt: new Date().toISOString(), settings: {}, unavailable: {} };
      const reportPath = join(__dirname, 'router-config-report.json');
      const queries = [
        ['router', 'getInfo'],
        ['lan', 'getLANConfig'],
        ['wan', 'getWANConfig'],
        ['guestWifi24GHzEnabled', 'getGuestWifiEnabled'],
        ['guestWifi5GHzEnabled', 'get5GGuestWifiEnabled'],
        ['channel24GHz', 'getChannelInfo'],
        ['channel5GHz', 'get5GChannelInfo'],
        ['portMappings', 'getPortMappingInfo'],
        ['accessControlEnabled', 'getBlockDeviceEnableStatus'],
        ['qosEnabled', 'getQoSEnableStatus'],
        ['trafficMeterEnabled', 'getTrafficMeterEnabled'],
        ['timeZone', 'getTimeZoneInfo'],
        ['attachedDevices', 'getAttachedDevices'],
      ];
      const redact = (_key, value) => {
        if (/password|passphrase|psk|secret|securitykey|serialnumber|session|cookie|token/i.test(_key)) {
          return '[redacted]';
        }
        return typeof value === 'string' ? value.split(password).join('[redacted]') : value;
      };
      for (const [name, method] of queries) {
        process.stderr.write(`Reading ${name}... `);
        try {
          report.settings[name] = await router[method]();
          process.stderr.write('OK\n');
        } catch (error) {
          report.unavailable[name] = error.message;
          process.stderr.write('unavailable\n');
        }
        writeFileSync(reportPath, JSON.stringify(report, redact, 2) + '\n', { mode: 0o600 });
        chmodSync(reportPath, 0o600);
      }
      console.log(`Configuration report saved to ${reportPath}`);
      return;
    }
    const result = command === 'info'
      ? await router.getInfo()
      : await router.getAttachedDevices();
    console.log(JSON.stringify(result, null, 2));
  } finally {
    if (router.loggedIn) await router.logout().catch(() => {});
    router.password = undefined;
    password = undefined;
  }
}

main().catch(error => {
  console.error(`Orbi: ${error.message}`);
  process.exitCode = 1;
});
