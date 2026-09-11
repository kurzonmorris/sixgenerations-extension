-- 0001 — the initial schema.
--
-- Straight from docs/DATA_MODEL.md. Two conventions throughout:
--
--   * money is INTEGER PENCE. Never a float, never pounds. 1250 is £12.50.
--   * dates are ISO-8601 TEXT, "2026-09-11" or "2026-09-11T14:03:00".
--     The old ledger stores "7.9.26" as text with a misleading cell format
--     (docs/EXISTING_LEDGER.md section 5) — importing converts, it does not copy.
--
-- Nothing is ever deleted. Rows change status. See section 3 of DATA_MODEL.md.

-- The garment. One row each, for life.
CREATE TABLE item (
  itemId          TEXT PRIMARY KEY,          -- internal surrogate, never shown
  sku             TEXT NOT NULL UNIQUE,      -- "13-8 24". Permanent, never recycled
  status          TEXT NOT NULL DEFAULT 'draft',
  title           TEXT NOT NULL DEFAULT '',
  description     TEXT NOT NULL DEFAULT '',
  brand           TEXT NOT NULL DEFAULT '',
  conditionNote   TEXT NOT NULL DEFAULT '',  -- your words, not a platform's list
  price           INTEGER,                   -- pence
  currency        TEXT NOT NULL DEFAULT 'GBP',
  cost            INTEGER,                   -- pence, usually derived from a lot
  lotId           TEXT REFERENCES lot(lotId),
  dateAdded       TEXT NOT NULL,
  dateListed      TEXT,
  dateSold        TEXT,
  weightGrams     INTEGER,
  parcelSize      TEXT,
  notes           TEXT NOT NULL DEFAULT '',  -- private, never shown to a buyer
  CHECK (status IN ('draft','needs_info','on_sale','reserved','sold','posted',
                    'completed','archived','removed'))
);
CREATE INDEX itemStatusIndex ON item(status);
CREATE INDEX itemBrandIndex  ON item(brand);
CREATE INDEX itemListedIndex ON item(dateListed);

-- Anything a garment can have more than one of: sizes in four systems, two
-- colours, a list of materials, a set of measurements.
CREATE TABLE itemAttribute (
  attributeId   INTEGER PRIMARY KEY,
  itemId        TEXT NOT NULL REFERENCES item(itemId),
  attribute     TEXT NOT NULL,               -- size | colour | material | measurement | ...
  value         TEXT NOT NULL,               -- "12" | "Navy" | "wool" | "chest"
  system        TEXT NOT NULL DEFAULT '',    -- UK | EU | US | IT | letter | cm | inches
  numericValue  REAL,                        -- for measurements and sorting
  source        TEXT NOT NULL DEFAULT 'manual',
  isPrimary     INTEGER NOT NULL DEFAULT 0,  -- the one to show when only one fits
  position      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX attributeItemIndex  ON itemAttribute(itemId, attribute);
CREATE INDEX attributeValueIndex ON itemAttribute(attribute, value);

-- A garment sits in a different category on every platform.
CREATE TABLE itemCategory (
  categoryRowId INTEGER PRIMARY KEY,
  itemId        TEXT NOT NULL REFERENCES item(itemId),
  platform      TEXT NOT NULL,               -- vinted | ebay | shopify | internal
  categoryPath  TEXT NOT NULL,               -- "Women / Dresses / Midi dresses"
  categoryId    TEXT NOT NULL DEFAULT '',    -- the platform's own id, where there is one
  isPrimary     INTEGER NOT NULL DEFAULT 0   -- eBay needs exactly one leaf
);
CREATE INDEX categoryItemIndex ON itemCategory(itemId);

-- The item is the garment. The listing is where it is being sold.
CREATE TABLE listing (
  listingId     INTEGER PRIMARY KEY,
  itemId        TEXT NOT NULL REFERENCES item(itemId),
  platform      TEXT NOT NULL,               -- vinted | ebay | shopify
  externalId    TEXT NOT NULL DEFAULT '',
  url           TEXT NOT NULL DEFAULT '',
  state         TEXT NOT NULL DEFAULT 'not_listed',
  price         INTEGER,                     -- pence; may differ per platform on purpose
  listedAt      TEXT,
  endedAt       TEXT,
  lastSyncedAt  TEXT,
  contentHash   TEXT NOT NULL DEFAULT '',    -- so nothing is pushed twice
  lastError     TEXT NOT NULL DEFAULT '',    -- the platform's own words, verbatim
  UNIQUE (itemId, platform),
  CHECK (state IN ('not_listed','draft','live','ended','sold','error','held'))
);
CREATE INDEX listingPlatformIndex ON listing(platform, state);

-- Photos, at full resolution, numbered exactly as they were first set.
CREATE TABLE itemImage (
  imageId     INTEGER PRIMARY KEY,
  itemId      TEXT NOT NULL REFERENCES item(itemId),
  position    INTEGER NOT NULL,              -- 1, 2, 3 ... the original order
  role        TEXT NOT NULL DEFAULT 'photo', -- photo | label | flaw | measurement | packed_parcel
  filePath    TEXT NOT NULL,
  sourceUrl   TEXT NOT NULL DEFAULT '',
  sha256      TEXT NOT NULL DEFAULT '',      -- never fetch or upload the same bytes twice
  width       INTEGER,
  height      INTEGER,
  bytes       INTEGER,
  platformIds TEXT NOT NULL DEFAULT '',      -- JSON: what each platform called its copy
  UNIQUE (itemId, position)
);
CREATE INDEX imageHashIndex ON itemImage(sha256);

-- One row per sale.
CREATE TABLE salesOrder (
  orderId            TEXT PRIMARY KEY,
  platform           TEXT NOT NULL,
  platformOrderRef   TEXT NOT NULL DEFAULT '',
  itemId             TEXT REFERENCES item(itemId),
  legacyName         TEXT NOT NULL DEFAULT '', -- the old ledger names items in free text
  soldPrice          INTEGER,                  -- pence
  postageCharged     INTEGER,
  postageCost        INTEGER,
  platformFees       INTEGER,                  -- NULL means "not told", never estimated
  netReceived        INTEGER,
  buyerName          TEXT NOT NULL DEFAULT '', -- personal data, see DATA_MODEL.md section 6
  buyerUsername      TEXT NOT NULL DEFAULT '',
  deliveryAddress    TEXT NOT NULL DEFAULT '',
  soldAt             TEXT,
  postedAt           TEXT,
  deliveredAt        TEXT,
  completedAt        TEXT,
  carrier            TEXT NOT NULL DEFAULT '',
  trackingNumber     TEXT NOT NULL DEFAULT '',
  trackingStatus     TEXT NOT NULL DEFAULT '',
  lastTrackingCheck  TEXT,
  parcelPhotoImageId INTEGER REFERENCES itemImage(imageId),
  status             TEXT NOT NULL DEFAULT 'sold',
  CHECK (status IN ('sold','awaiting_post','posted','in_transit','delivered',
                    'completed','issue','returned'))
);
CREATE INDEX orderSoldIndex   ON salesOrder(soldAt);
CREATE INDEX orderStatusIndex ON salesOrder(status);
CREATE INDEX orderItemIndex   ON salesOrder(itemId);

-- Buyer conversations, kept with the sale.
CREATE TABLE message (
  messageId   INTEGER PRIMARY KEY,
  orderId     TEXT REFERENCES salesOrder(orderId),
  itemId      TEXT REFERENCES item(itemId),
  platform    TEXT NOT NULL,
  direction   TEXT NOT NULL,                -- in | out
  sentAt      TEXT,
  author      TEXT NOT NULL DEFAULT '',
  body        TEXT NOT NULL DEFAULT '',
  attachments TEXT NOT NULL DEFAULT ''      -- JSON
);
CREATE INDEX messageOrderIndex ON message(orderId);

-- Stock arrives in bags and boxes. Per-item cost is always apportioned.
CREATE TABLE lot (
  lotId               TEXT PRIMARY KEY,
  purchasedOn         TEXT,
  source              TEXT NOT NULL DEFAULT '',
  lotCost             INTEGER,              -- pence for the whole lot
  itemCount           INTEGER,
  apportionmentMethod TEXT NOT NULL DEFAULT 'even',
  notes               TEXT NOT NULL DEFAULT '',
  CHECK (apportionmentMethod IN ('even','weighted','lot_only'))
);

CREATE TABLE purchase (
  purchaseId TEXT PRIMARY KEY,
  lotId      TEXT REFERENCES lot(lotId),
  purchasedOn TEXT,
  source     TEXT NOT NULL DEFAULT '',
  totalCost  INTEGER,                       -- pence
  itemCount  INTEGER,
  notes      TEXT NOT NULL DEFAULT ''
);

-- Posting trips and petrol: profit = sold - (stock + petrol), exactly as the
-- existing books already work it out. See docs/EXISTING_LEDGER.md section 3.
CREATE TABLE postingTrip (
  tripId        INTEGER PRIMARY KEY,
  tripDate      TEXT,
  trips         INTEGER NOT NULL DEFAULT 1,
  litresPerTrip REAL NOT NULL DEFAULT 0.959,
  pencePerLitre INTEGER,
  notes         TEXT NOT NULL DEFAULT ''
);

-- Every change, so a run can be explained afterwards and undone.
CREATE TABLE event (
  eventId    INTEGER PRIMARY KEY,
  happenedAt TEXT NOT NULL,
  actor      TEXT NOT NULL DEFAULT 'system',  -- system | user | vinted | ebay | shopify
  action     TEXT NOT NULL,
  subject    TEXT NOT NULL DEFAULT '',        -- usually an itemId or orderId
  field      TEXT NOT NULL DEFAULT '',
  valueBefore TEXT NOT NULL DEFAULT '',
  valueAfter  TEXT NOT NULL DEFAULT '',
  detail     TEXT NOT NULL DEFAULT ''
);
CREATE INDEX eventSubjectIndex ON event(subject, happenedAt);

-- Search across everything at once: "do you have anything with velvet in it?"
-- Contentless FTS, rebuilt per item by reindexItem() in core/database.py. A
-- trigger on `item` alone would miss attribute and category changes, so the
-- rebuild is explicit rather than clever.
CREATE VIRTUAL TABLE itemSearch USING fts5(
  itemId UNINDEXED,
  body,
  tokenize = 'unicode61 remove_diacritics 2'
);
