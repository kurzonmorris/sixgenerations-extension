/**
 * The normalised garment.
 *
 * Both adapters convert their platform's shape into this one, so the diff engine
 * never has to know whether a field came from Vinted or Shopify. Clothing-specific
 * attributes (size, brand, condition, colour) are first-class rather than being
 * buried in generic option arrays — that is the main thing the generic sync tools
 * get wrong for a wardrobe.
 */

import { parseStorageCode } from './storageCode.js';

/** @typedef {'active'|'sold'|'draft'|'hidden'|'unknown'} ItemStatus */

export function makeItem(fields = {}) {
  return {
    sku: fields.sku ?? '',
    // Parsed from the description unless a connector supplies it directly.
    storageCode: fields.storageCode ?? parseStorageCode(fields.description),
    source: fields.source ?? 'unknown', // 'vinted' | 'shopify'
    sourceId: fields.sourceId ?? '',
    variantId: fields.variantId ?? '',
    url: fields.url ?? '',

    title: fields.title ?? '',
    description: fields.description ?? '',

    price: Number.isFinite(fields.price) ? fields.price : null,
    currency: fields.currency ?? 'GBP',

    quantity: Number.isFinite(fields.quantity) ? fields.quantity : 0,
    status: fields.status ?? 'unknown',

    brand: fields.brand ?? '',
    size: fields.size ?? '',
    colour: fields.colour ?? '',
    condition: fields.condition ?? '',
    category: fields.category ?? '',
    material: fields.material ?? '',

    images: Array.isArray(fields.images) ? fields.images : [],
    updatedAt: fields.updatedAt ?? null,
    raw: fields.raw ?? null, // untouched platform payload, kept for debugging
  };
}

/** Money is compared in integer minor units to dodge float drift. */
export function toMinorUnits(amount) {
  if (amount === null || amount === undefined || amount === '') return null;
  const n = typeof amount === 'string' ? Number.parseFloat(amount) : amount;
  return Number.isFinite(n) ? Math.round(n * 100) : null;
}

export function fromMinorUnits(minor) {
  return minor === null || minor === undefined ? null : minor / 100;
}

/**
 * Vinted and Shopify spell sizes differently ("UK 10", "10", "M / UK 10"…).
 * Normalising before comparison stops the engine reporting phantom differences.
 */
export function normaliseSize(value) {
  return String(value ?? '')
    .toLowerCase()
    .replace(/\buk\b|\bsize\b/g, '')
    .replace(/[^a-z0-9]/g, '')
    .trim();
}

export function normaliseText(value) {
  return String(value ?? '').replace(/\s+/g, ' ').trim();
}

/** Cheap, stable hash used to tell "content changed" from "content identical". */
export function hashItem(item, fields) {
  const material = fields.map((field) => {
    const value = item[field];
    if (field === 'size') return normaliseSize(value);
    if (field === 'price') return String(toMinorUnits(value));
    if (Array.isArray(value)) return value.join('|');
    return normaliseText(value);
  }).join('');

  let h = 2166136261;
  for (let i = 0; i < material.length; i += 1) {
    h ^= material.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16);
}

/**
 * The shared key, in order of trustworthiness:
 *
 *   1. storage code — on every item, on both platforms. The real key.
 *   2. SKU field    — only some items have one, and only Shopify has the field.
 *   3. title + size — a guess. Reported so it is visible, but never written from.
 *
 * Both sides derive the key the same way, so two listings pair when their best
 * available key agrees.
 */
export function keyFor(item) {
  if (item.storageCode) return `loc:${item.storageCode}`;
  if (item.sku) return item.sku.trim().toLowerCase();
  const title = normaliseText(item.title).toLowerCase();
  const size = normaliseSize(item.size);
  return title ? `title:${title}${size ? `:${size}` : ''}` : '';
}

/** How confident the pairing is — surfaced in the plan so guesses are obvious. */
export function keyConfidence(item) {
  if (item.storageCode) return 'storage-code';
  if (item.sku) return 'sku';
  if (normaliseText(item.title)) return 'title-guess';
  return 'none';
}
