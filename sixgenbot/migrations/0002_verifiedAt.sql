-- 0002 — record that a person has checked an item.
--
-- The backlog is two lists: items that came off a live listing, and items that
-- have never been online. The second lot need going through one at a time —
-- not because fields are missing (some are complete) but because nobody has
-- confirmed them.
--
-- `status = needs_info` says a field is empty. This says nobody has looked.
-- Null means unchecked, which is the right default for everything imported.

ALTER TABLE item ADD COLUMN verifiedAt TEXT;

CREATE INDEX itemVerifiedIndex ON item(verifiedAt);
