import { createHash } from 'node:crypto';
import { request as httpsRequest } from 'node:https';
import { createConnection } from 'node:net';
import { connect, type TLSSocket } from 'node:tls';
import { OrbiError, validateHost } from './config.js';

export const SUPPORTED = { model: 'RBR850', firmware: 'V7.2.8.8_5.1.24', sealVersion: 'v2.2.9.6-0-gc6614a48' } as const;
export type Reply = { status: number; body: string };
export type Transport = (method: 'GET' | 'POST', path: string, body?: string) => Promise<Reply>;
const digest = (raw: Buffer): string => createHash('sha256').update(raw).digest('hex');

export function validateRsaKey(value: string): string {
  const match = /^ssh-rsa ([A-Za-z0-9+/]+={0,2})(?: [A-Za-z0-9_.@ -]+)?$/.exec(value.trim());
  try {
    if (!match) throw new Error();
    const blob = Buffer.from(match[1]!, 'base64'); let offset = 0;
    const field = (): Buffer => {
      if (offset + 4 > blob.length) throw new Error();
      const length = blob.readUInt32BE(offset); offset += 4;
      if (length < 1 || offset + length > blob.length) throw new Error();
      const data = blob.subarray(offset, offset + length); offset += length; return data;
    };
    if (field().toString() !== 'ssh-rsa') throw new Error();
    field(); const modulus = field();
    let first = 0; while (modulus[first] === 0) first++;
    const bits = (modulus.length - first - 1) * 8 + Math.floor(Math.log2(modulus[first] || 0)) + 1;
    if (offset !== blob.length || bits < 2048 || bits > 16384) throw new Error();
    return `ssh-rsa ${blob.toString('base64')}`;
  } catch { throw new OrbiError('INVALID_PUBLIC_KEY', 'Expected one RSA public key of at least 2048 bits, with no shell syntax in its comment.'); }
}

export function keyFingerprint(publicKey: string): string {
  const key = validateRsaKey(publicKey);
  return 'SHA256:' + createHash('sha256').update(Buffer.from(key.split(' ')[1]!, 'base64')).digest('base64').replace(/=+$/, '');
}

export function enrollmentPayload(password: string, publicKey: string): string {
  if (!password || /[\\\0\r\n]/.test(password) || /^-[neE]+$/.test(password)) {
    throw new OrbiError('UNREPRESENTABLE_PASSWORD', 'This password cannot be safely represented by the tested firmware enrollment handler. No request was sent.');
  }
  // This firmware feeds the password through an unquoted `echo -n` shell command.
  // Encode ONE literal shell word; never interpolate the raw password into a command.
  const literal = "'" + password.replaceAll("'", "'\\''") + "'";
  return JSON.stringify({ username: 'admin', password: literal, pubkey: validateRsaKey(publicKey) });
}

export function probeSsh(host: string): Promise<string | null> {
  validateHost(host);
  return new Promise((resolve, reject) => {
    const socket = createConnection({ host, port: 22 }); let data = '';
    const done = (value?: string | null, error?: Error): void => { socket.destroy(); if (error) reject(error); else resolve(value ?? null); };
    socket.setTimeout(4000, () => done(undefined, new OrbiError('SSH_UNAVAILABLE', 'SSH preflight timed out. Enrollment was not attempted.')));
    socket.on('data', chunk => {
      data += chunk.toString('utf8');
      if (data.includes('\n') || data.length >= 256) done(data.split('\n')[0]!.replace(/[^\x20-\x7e]/g, '').slice(0, 256));
    });
    socket.on('end', () => done(data || 'TCP 22 occupied'));
    socket.on('error', error => {
      if ((error as NodeJS.ErrnoException).code === 'ECONNREFUSED') done(null);
      else done(undefined, new OrbiError('SSH_UNAVAILABLE', 'SSH preflight failed. Enrollment was not attempted.'));
    });
  });
}

export function readTlsFingerprint(host: string, port = 443): Promise<string> {
  validateHost(host);
  return new Promise((resolve, reject) => {
    const socket = connect({ host, port, rejectUnauthorized: false });
    socket.setTimeout(8000, () => socket.destroy(new Error('timeout')));
    socket.once('secureConnect', () => {
      const raw = socket.getPeerCertificate().raw;
      if (!raw) { socket.destroy(new Error('certificate unavailable')); return; }
      resolve(digest(raw)); socket.destroy();
    });
    socket.once('error', () => reject(new OrbiError('HTTPS_UNAVAILABLE', 'Could not inspect the router HTTPS certificate. No credentials were sent.')));
  });
}

export function pinnedRequest(host: string, pin: string, method: 'GET' | 'POST', path: string, body?: string, port = 443): Promise<Reply> {
  validateHost(host);
  if (!/^[a-f0-9]{64}$/.test(pin)) throw new OrbiError('INVALID_TLS_PIN', 'Invalid router certificate fingerprint.');
  return new Promise((resolve, reject) => {
    let failure: OrbiError | undefined;
    const req = httpsRequest({ hostname: host, port, method, path, agent: false, rejectUnauthorized: false,
      headers: body === undefined ? {} : { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) } }, res => {
      const chunks: Buffer[] = []; let length = 0;
      res.on('data', (chunk: Buffer) => {
        length += chunk.length;
        if (length > 65536) { failure = new OrbiError('HTTPS_RESPONSE_TOO_LARGE', 'Router response exceeded the size limit. Do not repeat enrollment automatically.'); res.destroy(); req.destroy(failure); }
        else chunks.push(chunk);
      });
      res.once('error', () => reject(failure || new OrbiError('HTTPS_FAILED', 'Router response was interrupted. Do not repeat enrollment automatically.')));
      res.once('end', () => resolve({ status: res.statusCode || 0, body: Buffer.concat(chunks).toString('utf8') }));
    });
    const timer = setTimeout(() => req.destroy(new Error('timeout')), 8000);
    req.once('close', () => clearTimeout(timer));
    req.once('error', () => reject(failure || new OrbiError('HTTPS_FAILED', 'Router HTTPS request failed. Enrollment is never retried automatically.')));
    req.once('socket', socket => {
      (socket as TLSSocket).once('secureConnect', () => {
        const raw = (socket as TLSSocket).getPeerCertificate().raw;
        if (!raw || digest(raw) !== pin) {
          failure = new OrbiError('TLS_IDENTITY_CHANGED', 'Router certificate identity changed. No credentials were sent; verify its identity before proceeding.');
          req.destroy(failure); return;
        }
        // Do not queue headers or a credential body until this connection is pinned.
        req.end(body);
      });
    });
  });
}

export async function inspectTarget(transport: Transport): Promise<void> {
  const settings = await transport('GET', '/currentsetting.htm');
  const fields = Object.fromEntries(settings.body.split(/\r?\n/).filter(line => line.includes('=')).map(line => { const i = line.indexOf('='); return [line.slice(0, i), line.slice(i + 1).trim()]; }));
  if (settings.status !== 200 || fields.Model !== SUPPORTED.model || fields.Firmware !== SUPPORTED.firmware) {
    throw new OrbiError('UNSUPPORTED_FIRMWARE', `SSH enrollment firmware is validated only for ${SUPPORTED.model} ${SUPPORTED.firmware}. No configuration change was sent.`);
  }
  const meta = await transport('GET', '/api/meta');
  let version: unknown;
  try { version = JSON.parse(meta.body).seal_version; } catch { /* handled below */ }
  if (meta.status !== 200 || typeof version !== 'string' || version !== SUPPORTED.sealVersion) {
    throw new OrbiError('UNSUPPORTED_SEAL', 'Router SeAL version does not match the validated enrollment implementation.');
  }
}

export async function enrollOnce(transport: Transport, password: string, publicKey: string): Promise<void> {
  const payload = enrollmentPayload(password, publicKey);
  await inspectTarget(transport);
  const response = await transport('POST', '/api/v1/enable_ssh', payload);
  if (response.status !== 200) throw new OrbiError('ENROLLMENT_FAILED', 'Enrollment was not confirmed. No automatic retry: repeated rejected credentials can lock this endpoint.');
}
