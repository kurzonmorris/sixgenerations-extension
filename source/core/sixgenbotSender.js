/**
 * Sending a Vinted wardrobe read to the sixgenbot server.
 *
 * The server owns the database; the extension owns the browser session. This is
 * the hand-over between them, and it only ever goes one way: the extension
 * sends what it read, and the server answers with what that read *would* do.
 *
 * **Nothing is changed by sending.** The server stores the read and works out a
 * plan; applying it is a button on its own page. So a read that arrives at the
 * wrong moment, or twice, cannot alter the catalogue.
 *
 * Permission for the server's address is asked for at the moment of sending,
 * not at install: the extension ships able to reach Vinted and Shopify and
 * nothing else, and the user's own server is added when they name it.
 */

export function tidyUrl(url) {
  const trimmed = String(url ?? '').trim().replace(/\/+$/, '');
  if (!trimmed) return '';
  return /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
}

/** Chrome needs an origin pattern, not a bare address. */
export function originPattern(url) {
  const tidy = tidyUrl(url);
  if (!tidy) return '';
  try {
    return `${new URL(tidy).origin}/*`;
  } catch {
    return '';
  }
}

export async function askPermission(url, permissions = chrome.permissions) {
  const pattern = originPattern(url);
  if (!pattern) throw new Error('That server address cannot be understood.');
  if (await permissions.contains({ origins: [pattern] })) return true;
  return permissions.request({ origins: [pattern] });
}

/**
 * Posts the read. Returns the server's own words about what it would do.
 */
export async function sendWardrobe(url, items, { fetcher = fetch } = {}) {
  const tidy = tidyUrl(url);
  if (!tidy) throw new Error('No server address has been set yet.');
  if (!Array.isArray(items)) throw new Error('There is nothing to send.');

  const reply = await fetcher(`${tidy}/vinted/read`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      items,
      readAt: new Date().toISOString(),
      from: 'extension',
    }),
  });

  if (!reply.ok) {
    throw new Error(`The server at ${tidy} answered ${reply.status}.`);
  }
  return reply.json();
}
