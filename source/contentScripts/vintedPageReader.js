/**
 * Vinted content script.
 *
 * Runs inside a signed-in Vinted tab and answers questions from the service
 * worker. Reads use the site's own JSON endpoints with the user's session
 * (same-origin, cookies included) and fall back to reading the rendered
 * wardrobe grid when an endpoint moves.
 *
 * The endpoint shapes below are Vinted-internal and unversioned. Each strategy
 * reports which path produced the data (`via`) so a mismatch after a site change
 * is visible in the activity log instead of silently returning nothing.
 */

const MSG = {
  VINTED_PROBE: 'vinted-probe',
  VINTED_SCRAPE_WARDROBE: 'vinted-scrape-wardrobe',
};

const PER_PAGE = 96;
// 2000+ garments at 96 a page is ~22 requests; this cap is headroom, not a target.
const MAX_PAGES = 80;
// Vinted sits behind DataDome (docs/PROJECT_INFO.md §2.4). Paced requests from a
// real signed-in session look like browsing; a burst of 20+ does not.
const PAGE_DELAY_MS = 900;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  const handler = {
    [MSG.VINTED_PROBE]: probe,
    [MSG.VINTED_SCRAPE_WARDROBE]: () => scrapeWardrobe(message),
  }[message?.type];

  if (!handler) return false;

  Promise.resolve()
    .then(handler)
    .then(sendResponse)
    .catch((error) => sendResponse({ error: String(error?.message ?? error) }));
  return true; // keep the channel open for the async reply
});

// --- session -----------------------------------------------------------------

async function json(path) {
  const response = await fetch(path, {
    credentials: 'include',
    headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
  });
  if (!response.ok) throw new Error(`${path} -> HTTP ${response.status}`);
  return response.json();
}

/** Next.js hydration payload, when the page still ships one. */
function nextData() {
  try {
    const node = document.getElementById('__NEXT_DATA__');
    return node ? JSON.parse(node.textContent) : null;
  } catch {
    return null;
  }
}

function deepFind(value, predicate, depth = 0) {
  if (depth > 6 || value === null || typeof value !== 'object') return null;
  if (predicate(value)) return value;
  for (const child of Object.values(value)) {
    const hit = deepFind(child, predicate, depth + 1);
    if (hit) return hit;
  }
  return null;
}

async function currentUser() {
  // 1. hydration payload
  const user = deepFind(nextData(), (v) => typeof v.id === 'number' && typeof v.login === 'string' && 'item_count' in v);
  if (user) return { id: user.id, login: user.login, via: '__NEXT_DATA__' };

  // 2. session endpoint
  try {
    const data = await json('/api/v2/users/current');
    if (data?.user?.id) return { id: data.user.id, login: data.user.login, via: '/api/v2/users/current' };
  } catch { /* fall through */ }

  // 3. the profile link in the header
  const href = document.querySelector('a[href*="/member/"]')?.getAttribute('href') ?? '';
  const id = href.match(/\/member\/(\d+)/)?.[1];
  if (id) return { id: Number(id), login: href.split('-').slice(1).join('-'), via: 'header-link' };

  return null;
}

async function probe() {
  const user = await currentUser();
  return {
    signedIn: Boolean(user),
    userId: user?.id ?? null,
    username: user?.login ?? '',
    via: user?.via ?? null,
    domain: location.hostname,
    url: location.href,
  };
}

// --- wardrobe ----------------------------------------------------------------

async function scrapeWardrobe({ username } = {}) {
  const user = await currentUser();
  if (!user) return { error: 'Not signed in to Vinted in this tab.' };
  if (username && user.login && username.toLowerCase() !== String(user.login).toLowerCase()) {
    return { error: `Signed in as "${user.login}" but settings say "${username}".` };
  }

  try {
    const items = await viaApi(user.id);
    return { items, via: 'api', userId: user.id, username: user.login };
  } catch (error) {
    const items = viaDom();
    if (!items.length) throw error;
    return { items, via: 'dom', userId: user.id, username: user.login, apiError: String(error.message ?? error) };
  }
}

async function viaApi(userId) {
  const items = [];
  for (let page = 1; page <= MAX_PAGES; page += 1) {
    if (page > 1) await sleep(PAGE_DELAY_MS);
    const data = await json(`/api/v2/users/${userId}/items?page=${page}&per_page=${PER_PAGE}`);
    const batch = data.items ?? [];
    items.push(...batch.map(normaliseApiItem));
    if (batch.length < PER_PAGE) return items;
  }
  // Hitting the cap means the wardrobe is bigger than expected — say so loudly
  // rather than returning a silently truncated catalogue to the parity engine.
  throw new Error(
    `Vinted wardrobe exceeded ${MAX_PAGES * PER_PAGE} items — read stopped early and would be incomplete. Raise MAX_PAGES in vintedPageReader.js.`,
  );
}

/**
 * Maps a Vinted item payload onto the shared item shape (see lib/item.js).
 * Field names vary by locale/version, so each read is defensive.
 */
function normaliseApiItem(raw) {
  const price = Number.parseFloat(raw.price?.amount ?? raw.price ?? raw.total_item_price?.amount);
  const sold = Boolean(raw.is_closed || raw.is_sold || raw.item_closing_action === 'sold');
  const hidden = Boolean(raw.is_hidden);
  const photos = Array.isArray(raw.photos) ? raw.photos : raw.photo ? [raw.photo] : [];

  const description = (raw.description ?? '').replace(/\s+/g, ' ').trim();

  return {
    sku: '', // Vinted has no SKU field; the storage code is the key
    storageCode: extractStorageCode(description),
    source: 'vinted',
    sourceId: String(raw.id ?? ''),
    variantId: '',
    url: raw.url ?? raw.path ?? '',
    title: raw.title ?? '',
    description,
    price: Number.isFinite(price) ? price : null,
    currency: raw.price?.currency_code ?? raw.currency ?? 'GBP',
    quantity: sold ? 0 : 1, // Vinted listings are single-item by nature
    status: sold ? 'sold' : hidden ? 'hidden' : 'active',
    brand: raw.brand_title ?? raw.brand?.title ?? '',
    size: raw.size_title ?? raw.size ?? '',
    colour: raw.color1 ?? raw.colour ?? '',
    condition: raw.status ?? raw.condition ?? '',
    category: raw.catalog_title ?? '',
    material: raw.composition ?? '',
    images: photos.map((p) => p?.full_size_url ?? p?.url).filter(Boolean),
    updatedAt: raw.updated_at ?? null,
    raw: null, // dropped: the full payload is large and not needed downstream
  };
}

/**
 * The physical storage code at the end of every description — "13-8 24" meaning
 * column 13, box 8 high, item 24. This is the pairing key.
 *
 * ⚠ Kept in sync by hand with `parseStorageCode()` in core/storageCode.js.
 * Content scripts cannot import ES modules, so the pattern is duplicated rather
 * than shared. Change one, change the other —
 * tests/storageCode.test.mjs asserts the two agree.
 */
function extractStorageCode(description) {
  const match = String(description ?? '')
    .replace(/\s+/g, ' ')
    .trim()
    .match(/(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*[-–—\s]\s*(\d{1,4})[\s.,;:]*$/);

  return match ? `${Number(match[1])}-${Number(match[2])}-${Number(match[3])}` : '';
}

/** Last resort: read the wardrobe grid that is already on screen. */
function viaDom() {
  const cards = document.querySelectorAll('[data-testid$="--item-card"], .feed-grid__item');
  return [...cards].map((card) => {
    const link = card.querySelector('a[href*="/items/"]');
    const href = link?.getAttribute('href') ?? '';
    const text = card.textContent ?? '';
    const price = Number.parseFloat((text.match(/(\d+[.,]\d{2})/) ?? [])[1]?.replace(',', '.'));

    return {
      sku: '',
      // The grid does not render descriptions, so there is no code to read here.
      // DOM-fallback items can only ever match on title + size.
      storageCode: '',
      source: 'vinted',
      sourceId: href.match(/\/items\/(\d+)/)?.[1] ?? '',
      variantId: '',
      url: href,
      title: link?.getAttribute('title') ?? card.querySelector('[data-testid$="--description-title"]')?.textContent?.trim() ?? '',
      description: '',
      price: Number.isFinite(price) ? price : null,
      currency: 'GBP',
      quantity: /sold/i.test(text) ? 0 : 1,
      status: /sold/i.test(text) ? 'sold' : 'active',
      brand: card.querySelector('[data-testid$="--description-subtitle"]')?.textContent?.trim() ?? '',
      size: '',
      colour: '',
      condition: '',
      category: '',
      material: '',
      images: [...card.querySelectorAll('img')].map((img) => img.src).filter(Boolean),
      updatedAt: null,
      raw: null,
    };
  }).filter((item) => item.sourceId);
}
