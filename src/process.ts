import { execFile } from 'node:child_process';

export type Runner = (file: string, args: string[], input?: string) => Promise<{ stdout: string; stderr: string }>;

// No shell. Both execution time and output are bounded. Input is a fixed read script.
export const run: Runner = (file, args, input) => new Promise((resolve, reject) => {
  const child = execFile(file, args, { encoding: 'utf8', timeout: 12_000, killSignal: 'SIGKILL', maxBuffer: 128 * 1024 }, (error, stdout, stderr) => {
    if (error) reject(Object.assign(error, { stderr }));
    else resolve({ stdout, stderr });
  });
  child.stdin?.on('error', () => { /* Process exit is reported by execFile. */ });
  child.stdin?.end(input);
});
