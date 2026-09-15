-- 0003 — what the Crosslist import needs, and the truth about photo order.
--
-- Two things this records that nothing else could:
--
-- 1. `crosslistId` — the export's own row id, so running the import twice
--    updates rather than duplicates.
--
-- 2. `orderSource` on a photo. **Crosslist's photo order is not trustworthy.**
--    Vinted stores photos in the order the seller chose; Crosslist downloaded
--    them and kept them in whatever order suited it. So the order that arrives
--    with the import is a guess, the order read back from Vinted is the truth,
--    and an order set by hand is final. Without this column there is no way to
--    tell which of the three you are looking at.

ALTER TABLE item ADD COLUMN crosslistId TEXT;
ALTER TABLE item ADD COLUMN legacyCode  TEXT NOT NULL DEFAULT '';
ALTER TABLE item ADD COLUMN importNote  TEXT NOT NULL DEFAULT '';

CREATE UNIQUE INDEX itemCrosslistIndex ON item(crosslistId) WHERE crosslistId IS NOT NULL;
CREATE INDEX itemLegacyCodeIndex ON item(legacyCode);

-- 'crosslist' = a guess · 'vinted' = the seller's own order · 'manual' = set by hand
ALTER TABLE itemImage ADD COLUMN orderSource TEXT NOT NULL DEFAULT 'crosslist';
ALTER TABLE itemImage ADD COLUMN fetchedAt   TEXT;
ALTER TABLE itemImage ADD COLUMN fetchError  TEXT NOT NULL DEFAULT '';
