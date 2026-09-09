/**
 * The physical storage code — this project's pairing key.
 *
 * Every garment carries its location at the end of the listing description on
 * both platforms, in the form:
 *
 *     13-8 24     →  column 13, box 8 high, item 24
 *
 * The business calls this the SKU. It is on every item, which makes it a better
 * key than Shopify's SKU field (populated on only some items) and far better
 * than title + size.
 *
 * The item number is a per-box sequence that is **never reused**. A returned
 * garment keeps its number and goes back in the same box, so the same listing
 * can be re-uploaded unchanged. Boxes hold 20-40 items, so the number climbs
 * slowly, but it climbs forever: "5-6 17735" is a legitimate code and each box
 * has room for 99,999 items. Hence five digits, not four.
 *
 * Tolerated spellings, all normalising to "13-8-24":
 *     13-8 24     13-8-24     13 - 8 24     13-8  24.
 *
 * ⚠ The code describes where the garment physically is. If something is re-boxed
 * without both listings being updated, the pair silently breaks and both sides
 * report as one-sided. See docs/OPEN_QUESTIONS.md Q11.
 */

/**
 * Anchored to the end of the text, since that is where the code always sits.
 * Anchoring is what stops a size range like "10-12" mid-description matching.
 *
 * Item numbers run to five digits (99,999 per box) because they are never
 * recycled — see the note above.
 */
const TRAILING_CODE = /(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*[-–—\s]\s*(\d{1,5})[\s.,;:]*$/;

/** Normalised form used as the map key: "13-8-24". */
export function parseStorageCode(text) {
  if (!text) return '';
  const cleaned = String(text).replace(/\s+/g, ' ').trim();
  const match = cleaned.match(TRAILING_CODE);
  if (!match) return '';

  const [, column, box, item] = match;
  return `${Number(column)}-${Number(box)}-${Number(item)}`;
}

/** The form written into a listing description: "13-8 24". */
export function formatStorageCode(code) {
  const parts = String(code ?? '').split('-');
  return parts.length === 3 ? `${parts[0]}-${parts[1]} ${parts[2]}` : '';
}

/** Human-readable, for the popup and reports. */
export function describeStorageCode(code) {
  const parts = String(code ?? '').split('-');
  if (parts.length !== 3) return '';
  const [column, box, item] = parts;
  return `column ${column}, box ${box}, item ${item}`;
}

/**
 * Replaces the trailing code, or appends one if the description has none.
 * Needed by the Vinted write path (F-02/F-04), which must never lose the code.
 */
export function withStorageCode(description, code) {
  const formatted = formatStorageCode(code);
  if (!formatted) return description;

  const body = String(description ?? '').trimEnd();
  return parseStorageCode(body)
    ? body.replace(TRAILING_CODE, formatted)
    : `${body}\n\n${formatted}`;
}
