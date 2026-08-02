/**
 * Guards the version number against drifting between the four places it appears:
 * the root VERSION_v_x.x.x marker file, manifest.json's `version` and
 * `version_name`, and the top entry of docs/CHANGELOG.md.
 *
 * If this test fails after a version bump, one of them was missed — see
 * docs/VERSIONING.md for the full bump checklist.
 */

import test from 'node:test';
import assert from 'node:assert/strict';
import { readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const manifest = JSON.parse(readFileSync(join(root, 'manifest.json'), 'utf8'));

const markerFiles = readdirSync(root).filter((name) => name.startsWith('VERSION_v_'));

test('exactly one version marker file exists at the repo root', () => {
  assert.equal(markerFiles.length, 1, `found: ${markerFiles.join(', ') || 'none'}`);
});

test('the marker filename matches manifest.json', () => {
  assert.equal(markerFiles[0], `VERSION_v_${manifest.version}`);
});

test('manifest version_name is the v_ display form of version', () => {
  assert.equal(manifest.version_name, `v_${manifest.version}`);
});

test('the version is MAJOR.MINOR.PATCH', () => {
  assert.match(manifest.version, /^\d+\.\d+\.\d+$/);
});

test('the changelog leads with the current version', () => {
  const changelog = readFileSync(join(root, 'docs/CHANGELOG.md'), 'utf8');
  const firstEntry = changelog.match(/^## +(v_\d+\.\d+\.\d+)/m);
  assert.ok(firstEntry, 'no "## v_x.x.x" heading found in docs/CHANGELOG.md');
  assert.equal(firstEntry[1], `v_${manifest.version}`);
});
