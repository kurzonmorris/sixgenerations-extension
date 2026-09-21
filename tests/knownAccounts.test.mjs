/**
 * Making sure it is the right shop and the right Vinted account.
 *
 * The shop is being renamed within the year, and a Vinted username can change
 * any day, so every test here turns on one rule: **ids decide, names do not**.
 *
 * The real values, read from the live store on 2026-09-21:
 *   id               gid://shopify/Shop/94814568835   never changes
 *   myshopifyDomain  1kaa6a-ua.myshopify.com          never changes
 *   name             Six Generations                  changes on a rename
 *   primaryDomain    www.sixgenerations.co.uk         changes on a rename
 */

import test from 'node:test';
import assert from 'node:assert/strict';

import {
  checkAccount, isLocked, mayProceed, noAccount, rememberFrom,
} from '../source/core/knownAccounts.js';

const SHOP = { id: 'gid://shopify/Shop/94814568835', name: 'Six Generations' };

test('a fresh copy is tied to nothing', () => {
  assert.equal(isLocked(noAccount()), false);
});

test('the first connection is remembered', () => {
  const result = checkAccount(noAccount(), SHOP);
  assert.equal(result.state, 'first');
  assert.equal(mayProceed(result), true);

  const stored = rememberFrom(noAccount(), result);
  assert.equal(stored.id, SHOP.id);
  assert.ok(stored.firstSeenAt, 'the day it was tied is recorded');
});

test('the same shop connecting again is allowed', () => {
  const known = rememberFrom(noAccount(), checkAccount(noAccount(), SHOP));
  const result = checkAccount(known, SHOP);
  assert.equal(result.state, 'same');
  assert.equal(mayProceed(result), true);
});

test('renaming the shop is allowed, and said out loud', () => {
  const known = rememberFrom(noAccount(), checkAccount(noAccount(), SHOP));
  const renamed = { id: SHOP.id, name: 'Six Generations Vintage' };

  const result = checkAccount(known, renamed);

  assert.equal(result.state, 'renamed');
  assert.equal(mayProceed(result), true, 'a rename must never stop the run');
  assert.match(result.message, /renamed from "Six Generations" to "Six Generations Vintage"/);
});

test('the new name is kept, so the next run does not report the rename again', () => {
  const known = rememberFrom(noAccount(), checkAccount(noAccount(), SHOP));
  const renamed = { id: SHOP.id, name: 'Six Generations Vintage' };

  const after = rememberFrom(known, checkAccount(known, renamed));
  assert.equal(after.name, 'Six Generations Vintage');
  assert.equal(after.id, SHOP.id, 'the id never moves');
  assert.equal(after.firstSeenAt, known.firstSeenAt, 'the day it was tied does not reset');

  assert.equal(checkAccount(after, renamed).state, 'same');
});

test('a different shop is refused, even with the same name', () => {
  const known = rememberFrom(noAccount(), checkAccount(noAccount(), SHOP));
  const impostor = { id: 'gid://shopify/Shop/11111111111', name: 'Six Generations' };

  const result = checkAccount(known, impostor);

  assert.equal(result.state, 'different');
  assert.equal(mayProceed(result), false);
  assert.match(result.message, /Nothing was changed/);
});

test('a refused connection changes nothing that was recorded', () => {
  const known = rememberFrom(noAccount(), checkAccount(noAccount(), SHOP));
  const impostor = { id: 'gid://shopify/Shop/11111111111', name: 'Someone Else' };

  const after = rememberFrom(known, checkAccount(known, impostor));

  assert.deepEqual(after, known, 'a wrong shop must not overwrite the right one');
});

test('a connection that will not say who it is cannot proceed', () => {
  const result = checkAccount(noAccount(), { id: '', name: 'Six Generations' });
  assert.equal(mayProceed(result), false);
});

test('a Vinted account is checked by its number, not its username', () => {
  const known = rememberFrom(noAccount(), checkAccount(noAccount(), { id: 4821993, name: 'sixgen' }));

  assert.equal(checkAccount(known, { id: 4821993, name: 'sixgenerations' }).state, 'renamed');
  assert.equal(checkAccount(known, { id: 9999999, name: 'sixgen' }).state, 'different');
});

test('an id given as a number and as text is the same account', () => {
  const known = rememberFrom(noAccount(), checkAccount(noAccount(), { id: 4821993, name: 'sixgen' }));
  assert.equal(checkAccount(known, { id: '4821993', name: 'sixgen' }).state, 'same');
});
