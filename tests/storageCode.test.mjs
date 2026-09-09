/**
 * The storage code is this project's pairing key, so its parsing is the single
 * most load-bearing rule in the codebase. A false match pairs two unrelated
 * garments and edits the wrong listing.
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import {
  parseStorageCode,
  formatStorageCode,
  describeStorageCode,
  withStorageCode,
} from '../source/core/storageCode.js';
import { makeItem, keyFor, keyConfidence } from '../source/core/garmentItem.js';

test('reads the code from the end of a description', () => {
  assert.equal(parseStorageCode('Lovely wool coat, barely worn.\n\n13-8 24'), '13-8-24');
});

test('accepts the spellings that occur in real listings', () => {
  for (const written of ['13-8 24', '13-8-24', '13 - 8 24', '13-8  24', '13-8 24.', '13–8 24']) {
    assert.equal(parseStorageCode(`Nice jumper. ${written}`), '13-8-24', `failed on "${written}"`);
  }
});

test('reads long item numbers — they are never recycled, so they climb forever', () => {
  assert.equal(parseStorageCode('Vintage silk blouse. 5-6 17735'), '5-6-17735');
  assert.equal(parseStorageCode('Coat 13-8 99999'), '13-8-99999');
});

test('strips leading zeros so 03-08 04 and 3-8 4 are the same slot', () => {
  assert.equal(parseStorageCode('Coat 03-08 04'), parseStorageCode('Coat 3-8 4'));
});

test('only reads a code at the end, so mid-text numbers are ignored', () => {
  assert.equal(parseStorageCode('Fits size 10-12 nicely, lovely fabric'), '');
  assert.equal(parseStorageCode('Waist 30-32 34 inches, see photos for the hem'), '');
});

test('returns nothing when there is no code at all', () => {
  for (const text of ['', null, undefined, 'Just a plain description']) {
    assert.equal(parseStorageCode(text), '');
  }
});

test('formats back to the written form, and reads as English', () => {
  assert.equal(formatStorageCode('13-8-24'), '13-8 24');
  assert.equal(describeStorageCode('13-8-24'), 'column 13, box 8, item 24');
  assert.equal(formatStorageCode('nonsense'), '');
});

test('rewrites an existing code without disturbing the description', () => {
  const before = 'Lovely wool coat, barely worn.\n\n13-8 24';
  const after = withStorageCode(before, '14-2-7');
  assert.equal(parseStorageCode(after), '14-2-7');
  assert.ok(after.startsWith('Lovely wool coat, barely worn.'));
});

test('appends a code when the description has none', () => {
  const after = withStorageCode('A plain description', '14-2-7');
  assert.equal(parseStorageCode(after), '14-2-7');
});

test('an item parses its code straight out of its description', () => {
  const item = makeItem({ title: 'Wool coat', description: 'Barely worn. 13-8 24' });
  assert.equal(item.storageCode, '13-8-24');
  assert.equal(keyFor(item), 'loc:13-8-24');
  assert.equal(keyConfidence(item), 'storage-code');
});

test('the storage code outranks a SKU field, so both sides agree on the key', () => {
  const shopify = makeItem({ sku: 'COAT-001', description: 'Wool coat. 13-8 24' });
  const vinted = makeItem({ sku: '', storageCode: '13-8-24' });
  assert.equal(keyFor(shopify), keyFor(vinted));
});

test('a SKU is still used when no storage code is present', () => {
  const item = makeItem({ sku: 'COAT-001', description: 'No code here' });
  assert.equal(keyFor(item), 'coat-001');
  assert.equal(keyConfidence(item), 'sku');
});

/**
 * vintedPageReader.js runs as a content script and cannot import ES modules, so
 * it carries its own copy of the pattern. This test is what stops the two
 * drifting apart unnoticed.
 */
test('the content script pattern agrees with core/storageCode.js', () => {
  const here = dirname(fileURLToPath(import.meta.url));
  const source = readFileSync(join(here, '../source/contentScripts/vintedPageReader.js'), 'utf8');

  const body = source.match(/function extractStorageCode\(description\) \{[\s\S]*?\n\}/)?.[0];
  assert.ok(body, 'extractStorageCode() not found in vintedPageReader.js');

  // eslint-disable-next-line no-new-func -- reading the shipped implementation, not user input
  const extractStorageCode = new Function(`${body}; return extractStorageCode;`)();

  for (const text of [
    'Lovely wool coat, barely worn. 13-8 24',
    'Jumper 03-08 04',
    'Fits size 10-12 nicely, lovely fabric',
    'No code here',
    'Trailing punctuation 7-1 9.',
  ]) {
    assert.equal(extractStorageCode(text), parseStorageCode(text), `disagreed on "${text}"`);
  }
});
