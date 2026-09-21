/**
 * Shared constants: message names, storage keys, defaults.
 * Imported by the service worker and the extension pages (popup / options).
 */

export const MSG = {
  // popup/options -> background
  GET_STATE: 'get-state',
  RUN_SYNC: 'run-sync',
  CANCEL_SYNC: 'cancel-sync',
  TEST_SHOPIFY: 'test-shopify',
  TEST_VINTED: 'test-vinted',
  GET_LOGS: 'get-logs',
  CLEAR_LOGS: 'clear-logs',
  EXPORT_REPORT: 'export-report',
  SEND_TO_SIXGENBOT: 'send-to-sixgenbot',
  FORGET_ACCOUNT: 'forget-account',

  // background -> content script (Vinted tab)
  VINTED_PROBE: 'vinted-probe',
  VINTED_SCRAPE_WARDROBE: 'vinted-scrape-wardrobe',

  // background -> any listening page (broadcast)
  STATE_CHANGED: 'state-changed',
  LOG_APPENDED: 'log-appended',
};

export const STORAGE_KEYS = {
  SETTINGS: 'settings',
  LINKS: 'links', // sku -> { vintedId, shopifyProductId, shopifyVariantId, hashes... }
  LOGS: 'logs',
  LAST_RUN: 'lastRun',
  SNAPSHOT: 'snapshot', // last known normalised items per side
};

/** Sync direction for a given field group. */
export const DIRECTION = {
  SHOPIFY_TO_VINTED: 'shopify->vinted',
  VINTED_TO_SHOPIFY: 'vinted->shopify',
  OFF: 'off',
};

/** Nothing is written to a live store until the user turns dry run off. */
export const DEFAULT_SETTINGS = {
  shopify: {
    shopDomain: '', // e.g. my-store.myshopify.com
    accessToken: '', // Admin API access token of a custom app
    apiVersion: '2025-01',
    locationId: '', // inventory location gid, resolved on first connect
  },
  vinted: {
    domain: 'www.vinted.co.uk',
    username: '',
  },
  // The server on the home network that owns the database. Empty until it is
  // given an address, and nothing is sent anywhere until then.
  sixgenbot: {
    url: '', // e.g. http://tower:8770
  },
  // Which shop and which Vinted account this copy is tied to. Recorded on the
  // first connection and compared on every one after it. Ids, never names: the
  // shop is being renamed and a Vinted username can change any day.
  known: {
    shopify: { id: '', name: '', firstSeenAt: null },
    vinted: { id: '', name: '', firstSeenAt: null },
  },
  sync: {
    dryRun: true,
    intervalMinutes: 0, // 0 = manual only
    skuField: 'sku', // Shopify field that carries the shared key
    inventory: DIRECTION.VINTED_TO_SHOPIFY, // a Vinted sale is the usual "sold" signal
    price: DIRECTION.SHOPIFY_TO_VINTED,
    content: DIRECTION.SHOPIFY_TO_VINTED, // title / description / images
    createMissing: false, // create listings that only exist on one side
    archiveSold: true,
  },
  debug: {
    verbose: true,
    maxLogEntries: 500,
  },
};

export const LOG_LEVEL = {
  DEBUG: 'debug',
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error',
};
