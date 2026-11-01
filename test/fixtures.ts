import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

export function configAt(directory: string) {
  return { version: 1 as const, host: '192.168.1.1', identityFile: join(directory, 'id_rsa'),
    knownHostsFile: join(directory, 'known_hosts'), hostKeyAlias: 'orbi-mcp-router' };
}

// Synthetic native outputs: no household addresses, names, credentials or identifiers.
export const nativeStatus = `__ORBI_PLATFORM__
{"productName":"RBR850","wanIntf":"eth4"}
__ORBI_VERSION__
7.2.8.8
__ORBI_ODM__
5.1.24
__ORBI_UPTIME__
12345.50 40000.0
__ORBI_LOAD__
0.25 0.50 0.75 1/100 1234
__ORBI_MEMORY__
MemTotal:        800000 kB
MemFree:         300000 kB
MemAvailable:    400000 kB
__ORBI_ETHERNET__
Settings for eth4:
  Speed: 2500Mb/s
  Duplex: Full
  Link detected: yes
`;

export function syntheticRsa(): string {
  const wire = (buffer: Buffer): Buffer => { const size = Buffer.alloc(4); size.writeUInt32BE(buffer.length); return Buffer.concat([size, buffer]); };
  return 'ssh-rsa ' + Buffer.concat([wire(Buffer.from('ssh-rsa')), wire(Buffer.from([1, 0, 1])), wire(Buffer.concat([Buffer.from([0]), Buffer.alloc(256, 0xff)]))]).toString('base64');
}


export function testTempRoot(): string {
  const path = fileURLToPath(new URL('../../.cache/test/', import.meta.url));
  mkdirSync(path, { recursive: true });
  return path;
}
