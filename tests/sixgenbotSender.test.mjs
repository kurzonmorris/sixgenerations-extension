/**
 * Sending a Vinted wardrobe read to the server that owns the database.
 *
 * The hand-over is one way and changes nothing by itself: the server stores
 * the read and answers with what it would do.
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import { originPattern, sendWardrobe, tidyUrl } from '../source/core/sixgenbotSender.js';

test('an address typed without http still works', () => {
  assert.equal(tidyUrl('tower:8770'), 'http://tower:8770');
  assert.equal(tidyUrl('http://tower:8770/'), 'http://tower:8770');
  assert.equal(tidyUrl('https://tower:8770'), 'https://tower:8770');
  assert.equal(tidyUrl('  '), '');
});

test('the permission asked for is the server origin, nothing wider', () => {
  assert.equal(originPattern('tower:8770'), 'http://tower:8770/*');
  assert.equal(originPattern('http://192.168.1.10:8770/vinted'), 'http://192.168.1.10:8770/*');
  assert.equal(originPattern(''), '', 'no address means no permission is asked for');
});

test('nothing is sent when no address has been set', async () => {
  await assert.rejects(() => sendWardrobe('', [{}]), /No server address/);
});

test('the read is posted as JSON to the read endpoint', async () => {
  let seen = null;
  const fetcher = async (url, options) => {
    seen = { url, options };
    return { ok: true, json: async () => ({ stored: 'vinted-1.json', nothingWritten: true }) };
  };

  const answer = await sendWardrobe('tower:8770', [{ sourceId: '1' }], { fetcher });

  assert.equal(seen.url, 'http://tower:8770/vinted/read');
  assert.equal(seen.options.method, 'POST');
  const body = JSON.parse(seen.options.body);
  assert.equal(body.items.length, 1);
  assert.equal(body.from, 'extension');
  assert.ok(body.readAt, 'the time of the read is sent with it');
  assert.equal(answer.nothingWritten, true);
});

test('a server that refuses says so in words, not a status code alone', async () => {
  const fetcher = async () => ({ ok: false, status: 502 });
  await assert.rejects(
    () => sendWardrobe('tower:8770', [], { fetcher }),
    /server at http:\/\/tower:8770 answered 502/,
  );
});

test('no token or credential is ever put in the body', async () => {
  let body = null;
  const fetcher = async (_url, options) => {
    body = options.body;
    return { ok: true, json: async () => ({}) };
  };

  await sendWardrobe('tower:8770', [{ sourceId: '1', title: 'A dress' }], { fetcher });

  for (const word of ['token', 'accessToken', 'password', 'cookie']) {
    assert.ok(!body.toLowerCase().includes(word.toLowerCase()), `${word} must not be sent`);
  }
});
