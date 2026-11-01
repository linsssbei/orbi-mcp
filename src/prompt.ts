import { createInterface } from 'node:readline/promises';
import { Writable } from 'node:stream';
import { OrbiError } from './config.js';

export interface Prompts { ask(message: string, hidden?: boolean): Promise<string>; log(message: string): void }
export const terminalPrompts: Prompts = {
  log: message => { process.stderr.write(message + '\n'); },
  async ask(message, hidden = false) {
    if (!process.stdin.isTTY || !process.stderr.isTTY) throw new OrbiError('INTERACTIVE_REQUIRED', 'Run setup in an interactive terminal; never pass the router password as an argument.');
    const muted = new Writable({ write(_chunk, _encoding, callback) { callback(); } });
    const rl = createInterface({ input: process.stdin, output: hidden ? muted : process.stderr, terminal: true });
    const controller = new AbortController();
    rl.once('SIGINT', () => controller.abort());
    try {
      if (hidden) process.stderr.write(message);
      return await rl.question(hidden ? '' : message, { signal: controller.signal });
    } finally { rl.close(); if (hidden) process.stderr.write('\n'); }
  },
};
