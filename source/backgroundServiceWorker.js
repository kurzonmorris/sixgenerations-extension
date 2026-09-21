/**
 * Service worker: the only place that talks to both platforms.
 *
 * MV3 workers are killed when idle, so nothing durable is kept in module scope —
 * run state is transient by design and everything worth keeping goes to storage.
 */

import { MSG, DEFAULT_SETTINGS } from './core/messageTypes.js';
import { getSettings, saveSettings, getLastRun, getLinks, getSnapshot } from './core/settingsStore.js';
import { logger, getLogs, clearLogs } from './core/activityLog.js';
import { SyncRun } from './core/syncRunner.js';
import { VintedAdapter } from './connectors/vintedWardrobeConnector.js';
import { askPermission, sendWardrobe, tidyUrl } from './core/sixgenbotSender.js';
import { checkAccount, mayProceed, noAccount, rememberFrom } from './core/knownAccounts.js';
import { ShopifyAdapter } from './connectors/shopifyStoreConnector.js';

const ALARM_NAME = 'scheduled-sync';

/** Transient run state, mirrored to listeners via STATE_CHANGED. */
let current = { running: false, phase: 'idle', progress: null, error: null };
let activeRun = null;

function setState(patch) {
  current = { ...current, ...patch };
  chrome.runtime.sendMessage({ type: MSG.STATE_CHANGED, state: current }).catch(() => {});
}

chrome.runtime.onInstalled.addListener(async (details) => {
  const settings = await saveSettings({}); // materialises defaults on first install
  await logger.info(`Extension ${details.reason} (v${chrome.runtime.getManifest().version})`);
  await rescheduleAlarm(settings);
  if (details.reason === 'install') chrome.runtime.openOptionsPage();
});

chrome.runtime.onStartup.addListener(async () => {
  await rescheduleAlarm(await getSettings());
});

chrome.storage.onChanged.addListener(async (changes, area) => {
  if (area === 'local' && changes.settings) await rescheduleAlarm(await getSettings());
});

async function rescheduleAlarm(settings) {
  await chrome.alarms.clear(ALARM_NAME);
  const minutes = Number(settings.sync.intervalMinutes) || 0;
  if (minutes <= 0) return;
  chrome.alarms.create(ALARM_NAME, { periodInMinutes: minutes, delayInMinutes: minutes });
  logger.debug(`Scheduled sync every ${minutes} min`);
}

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) startSync({ source: 'schedule' });
});

/**
 * Confirms a platform is the one this copy is tied to, and records it the first
 * time. Throws before anything is read or written if it is a different account.
 *
 * Ids, never names: the shop is being renamed within the year and a Vinted
 * username can change any day, so a name is shown and never compared.
 */
async function confirmAccount(platform, found) {
  const settings = await getSettings();
  const known = settings.known?.[platform] ?? noAccount();
  const result = checkAccount(known, found);

  if (!mayProceed(result)) {
    await logger.error(`${platform}: ${result.message}`);
    throw new Error(result.message);
  }
  if (result.state === 'first' || result.state === 'renamed') {
    await saveSettings({ known: { [platform]: rememberFrom(known, result) } });
    await logger.info(`${platform}: ${result.message}`);
  }
  return result;
}

async function startSync({ source = 'manual', dryRunOverride } = {}) {
  if (current.running) return { ok: false, error: 'A sync is already running.' };

  setState({ running: true, phase: 'starting', error: null, progress: null });
  activeRun = new SyncRun({ onProgress: (progress) => setState({ phase: progress.phase, progress }) });

  try {
    const lastRun = await activeRun.run({ dryRunOverride });
    setState({ running: false, phase: 'idle', progress: null });
    return { ok: true, lastRun };
  } catch (error) {
    const message = String(error?.message ?? error);
    await logger.error(`Run aborted (${source}): ${message}`);
    setState({ running: false, phase: 'idle', error: message });
    return { ok: false, error: message };
  } finally {
    activeRun = null;
  }
}

const handlers = {
  async [MSG.GET_STATE]() {
    return {
      ok: true,
      state: current,
      settings: await getSettings(),
      lastRun: await getLastRun(),
      links: Object.keys(await getLinks()).length,
      snapshotAt: (await getSnapshot()).takenAt,
      version: chrome.runtime.getManifest().version,
    };
  },

  [MSG.RUN_SYNC](message) {
    return startSync({ source: 'popup', dryRunOverride: message.dryRun });
  },

  [MSG.CANCEL_SYNC]() {
    activeRun?.cancel();
    return { ok: true };
  },

  async [MSG.TEST_SHOPIFY]() {
    const settings = await getSettings();
    const result = await new ShopifyAdapter(settings).testConnection();
    // First successful connect picks a location so inventory writes have a home.
    if (!settings.shopify.locationId && result.suggestedLocationId) {
      await saveSettings({ shopify: { locationId: result.suggestedLocationId } });
    }
    await confirmAccount('shopify', { id: result.shopId, name: result.shop });
    await logger.info(`Shopify connected: ${result.shop} (${result.currency})`, result.locations);
    return { ok: true, result };
  },

  async [MSG.TEST_VINTED]() {
    const result = await new VintedAdapter(await getSettings()).testConnection();
    await confirmAccount('vinted', { id: result.userId, name: result.username });
    await logger.info(`Vinted connected as ${result.username || result.userId}`, { via: result.via });
    return { ok: true, result };
  },

  /**
   * Reads the wardrobe and hands it to the server that owns the database.
   *
   * Nothing is written by sending: the server stores the read and answers with
   * what it *would* do. Applying it is a button on the server's own page.
   */
  async [MSG.SEND_TO_SIXGENBOT]() {
    const settings = await getSettings();
    const url = tidyUrl(settings.sixgenbot?.url);
    if (!url) {
      throw new Error('Set the sixgenbot address in Settings first.');
    }
    if (!(await askPermission(url))) {
      throw new Error(`Permission to reach ${url} was not given.`);
    }

    const adapter = new VintedAdapter(settings);
    const who = await adapter.testConnection();
    await confirmAccount('vinted', { id: who.userId, name: who.username });

    const items = await adapter.fetchItems({ knownUserId: who.userId });
    const answer = await sendWardrobe(url, items);
    await logger.info(
      `Sent ${items.length} Vinted listings to ${url} — ${answer.wouldDo ?? 'stored'}`,
      { stored: answer.stored },
    );
    return { ok: true, sent: items.length, answer };
  },

  /** Deliberate, and only from the settings page: tie this copy to nothing. */
  async [MSG.FORGET_ACCOUNT]({ platform }) {
    await saveSettings({ known: { [platform]: noAccount() } });
    await logger.warn(`${platform}: forgotten. The next connection will be recorded as the one.`);
    return { ok: true };
  },

  async [MSG.GET_LOGS]() {
    return { ok: true, logs: await getLogs() };
  },

  async [MSG.CLEAR_LOGS]() {
    await clearLogs();
    return { ok: true };
  },

  /** Self-contained JSON dump — the handover point for any external monitor. */
  async [MSG.EXPORT_REPORT]() {
    const settings = await getSettings();
    return {
      ok: true,
      report: {
        generatedAt: new Date().toISOString(),
        version: chrome.runtime.getManifest().version,
        settings: redact(settings),
        state: current,
        lastRun: await getLastRun(),
        links: await getLinks(),
        logs: await getLogs(),
      },
    };
  },
};

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  const handler = handlers[message?.type];
  if (!handler) return false;

  Promise.resolve()
    .then(() => handler(message))
    .then(sendResponse)
    .catch((error) => sendResponse({ ok: false, error: String(error?.message ?? error) }));
  return true;
});

/** Never let the Admin token reach an export, the clipboard or a log line. */
function redact(settings) {
  const copy = structuredClone({ ...DEFAULT_SETTINGS, ...settings });
  copy.shopify.accessToken = settings.shopify.accessToken ? '***redacted***' : '';
  return copy;
}
