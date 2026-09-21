/**
 * Making sure it is *your* shop and *your* Vinted account, every time.
 *
 * Two different problems, and only one of them was covered.
 *
 * **Shopify.** An access token is issued by one store and cannot read another,
 * so the token itself is the real protection. What was missing is a check that
 * the store answering is the store you meant: paste a second store's token into
 * the box and everything would have carried on quietly against the wrong shop.
 *
 * **Vinted.** The extension reads whichever tab is signed in. The only check was
 * the username, typed into settings by hand.
 *
 * **A name is not an identity.** The shop is being renamed within the year, and
 * a Vinted username can change any day. So neither is used to decide anything.
 * What is recorded instead never changes:
 *
 *   * Shopify — the shop's globally unique id, `gid://shopify/Shop/94814568835`.
 *   * Vinted — the numeric user id.
 *
 * The name is kept alongside, shown on screen so a person can see what is meant,
 * and ignored by every comparison.
 *
 * First connection records the id. Every connection after it compares. A
 * mismatch stops the run — it never writes and then reports.
 */

export const PLATFORMS = ['shopify', 'vinted'];

/** What a fresh, unlocked platform looks like. */
export function noAccount() {
  return { id: '', name: '', firstSeenAt: null };
}

export function isLocked(known) {
  return Boolean(known?.id);
}

/**
 * Compares what answered against what was recorded.
 *
 * Returns one of:
 *   { state: 'first', ... }   nothing recorded yet — this becomes the one
 *   { state: 'same', ... }    the same account, whatever it is called now
 *   { state: 'renamed', ... } same id, different name — allowed, and worth saying
 *   { state: 'different', ... } a different account — stop
 */
export function checkAccount(known, found) {
  const foundId = String(found?.id ?? '').trim();
  const foundName = String(found?.name ?? '').trim();

  if (!foundId) {
    return { state: 'unknown', message: 'That connection did not say which account it is.' };
  }
  if (!isLocked(known)) {
    return {
      state: 'first',
      id: foundId,
      name: foundName,
      message: `Remembered ${foundName || foundId}. Every later connection is checked against it.`,
    };
  }
  if (String(known.id) !== foundId) {
    return {
      state: 'different',
      id: foundId,
      name: foundName,
      message: `This is a different account. Expected ${known.name || known.id}`
        + ` (${known.id}), found ${foundName || foundId} (${foundId}). Nothing was changed.`,
    };
  }
  if (known.name && foundName && known.name !== foundName) {
    return {
      state: 'renamed',
      id: foundId,
      name: foundName,
      message: `Same account, renamed from "${known.name}" to "${foundName}".`,
    };
  }
  return { state: 'same', id: foundId, name: foundName, message: `${foundName || foundId}.` };
}

/** True when the run may go ahead. A rename is fine; a different account is not. */
export function mayProceed(result) {
  return ['first', 'same', 'renamed'].includes(result?.state);
}

/** What to store after a connection that is allowed to proceed. */
export function rememberFrom(known, result) {
  if (!mayProceed(result)) return known ?? noAccount();
  return {
    id: result.id,
    name: result.name,
    firstSeenAt: isLocked(known) ? known.firstSeenAt : new Date().toISOString(),
  };
}
