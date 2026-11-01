import { loadConfig, publicError } from './config.js';
import { checkConnectionFiles } from './setup.js';
import { getRouterStatus } from './router.js';

export async function doctor(configPath: string) {
  try {
    const config = await loadConfig(configPath);
    await checkConnectionFiles(config);
    const status = await getRouterStatus(config);
    return { ready: true as const, checks: { configuration: 'ok', identity: 'ok', pinnedSsh: 'ok', telemetry: 'ok' },
      router: { model: status.model, firmware: status.firmware }, rebootPersistence: 'not_validated' as const };
  } catch (error) {
    return { ready: false as const, error: publicError(error), rebootPersistence: 'not_validated' as const };
  }
}
