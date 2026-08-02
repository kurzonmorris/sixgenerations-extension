/**
 * Single source of version truth.
 *
 * manifest.json holds the number (Chrome requires it there and it must be bare
 * digits). The root marker file `VERSION_v_0.1.0` makes the same number visible
 * in the file structure, and every UI surface reads it from here so there is
 * only ever one place to change.
 *
 * tests/versionConsistency.test.mjs fails the build if the manifest, the marker
 * file and the changelog ever disagree.
 *
 * Format: v_MAJOR.MINOR.PATCH — see docs/VERSIONING.md for when each moves.
 */

export function extensionVersion() {
  return chrome.runtime.getManifest().version;
}

/** The display form, e.g. "v_0.1.0". Used in the popup and settings pages. */
export function versionLabel() {
  return `v_${extensionVersion()}`;
}

/** Writes the version into every element carrying `data-version-label`. */
export function stampVersionInto(document) {
  const label = versionLabel();
  for (const node of document.querySelectorAll('[data-version-label]')) {
    node.textContent = label;
  }
  return label;
}
