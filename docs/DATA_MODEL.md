# Data Model — items, multiple values, images, and the four CSVs

How the data is shaped. Proposal, not built. The architecture it assumes is in
`docs/SYSTEM_ARCHITECTURE.md`.

---

## 1. The problem with one box per fact

You put it exactly right: *"size for example is different in different countries
and whether you use number or letters, or both. So each element needs a way to
store it all."*

Today's item shape (`source/core/garmentItem.js:15`) holds **one string per
field**: one size, one colour, one category. That is wrong for garments:

| Field | Real garments have |
|---|---|
| **Size** | UK 12, EU 40, US 8, "M", plus actual measurements — often all at once |
| **Category** | "Women > Dresses > Midi" on Vinted, a different leaf on eBay, several Shopify collections |
| **Colour** | Navy *and* white. Vinted allows two, eBay wants one, the customer sees both |
| **Material** | 70% wool, 30% polyester |
| **Condition** | Vinted's five words, eBay's own enumeration, your own note |
| **Flaws** | Several, each with a photo |
| **Measurements** | Chest, waist, length, sleeve, hem — the numbers that actually stop returns |

## 2. The shape

One item, with child tables for anything that can occur more than once. Written
as tables, but it is the same idea whether it ends up in SQLite or Postgres.

### 2.1 `item` — the garment itself, one row each

| Column | Notes |
|---|---|
| `item_id` | Internal surrogate, a UUID. Never shown |
| `sku` | `13-8 24` — column 13, box 4, item 24. **The business's own permanent identifier.** Never recycled: a returned garment keeps its SKU and goes back in the same box, so its listing can be re-uploaded unchanged. Item numbers run to five digits (99,999 per box) |
| `status` | `draft` · `needs_info` · `on_sale` · `reserved` · `sold` · `posted` · `completed` · `archived` · `removed` |
| `title` | |
| `description` | |
| `brand` | |
| `condition_note` | Your own words, separate from any platform's enumeration |
| `price` | Asking price, in pence |
| `currency` | |
| `cost` | What it cost you (from the purchases side) |
| `lot_id` | If it came in a job lot |
| `date_added` | When it entered the system |
| `date_listed` | **When it was uploaded** — you asked for this |
| `date_sold` | |
| `weight_grams`, `parcel_size` | Postage needs them |
| `notes` | Free text |

### 2.2 `item_attribute` — everything that can have more than one value

| Column | Example |
|---|---|
| `item_id` | |
| `attribute` | `size` · `colour` · `material` · `measurement` · `style` · `pattern` · `fit` · `era` |
| `value` | `12` · `40` · `Navy` · `wool` · `chest` |
| `system` | `UK` · `EU` · `US` · `IT` · `letter` · `cm` · `inches` — how to read the value |
| `numeric_value` | For measurements and sorting |
| `source` | `vinted` · `ebay` · `shopify` · `manual` · `inferred` |
| `is_primary` | The one to show when only one can be shown |
| `position` | Display order |

So one dress can carry `size UK 12`, `size EU 40`, `size letter M`,
`measurement chest 46 cm`, `measurement length 98 cm`, `colour Navy (primary)`,
`colour White` — and each platform is handed whichever ones it accepts.

### 2.3 `item_category` — because things sit in several

| Column | Example |
|---|---|
| `item_id` | |
| `platform` | `vinted` · `ebay` · `shopify` · `internal` |
| `category_path` | `Women / Dresses / Midi dresses` |
| `category_id` | The platform's own id, where there is one |
| `is_primary` | eBay needs exactly one leaf category |

### 2.4 `listing` — one row per platform per item

The item is the garment. The listing is where it is being sold.

| Column | Notes |
|---|---|
| `item_id`, `platform` | |
| `external_id` | Vinted item id, eBay offer/listing id, Shopify product+variant id |
| `url` | |
| `state` | `not_listed` · `draft` · `live` · `ended` · `sold` · `error` |
| `price` | Can differ per platform deliberately |
| `listed_at`, `ended_at` | |
| `last_synced_at`, `content_hash` | What was pushed, so nothing is pushed twice |
| `last_error` | The platform's own message, verbatim |

### 2.5 `item_image` — full detail, numbered in original order

| Column | Notes |
|---|---|
| `item_id` | |
| `position` | **1, 2, 3… exactly as originally set.** You asked for this specifically |
| `role` | `photo` · `label` · `flaw` · `measurement` · `packed_parcel` |
| `file_path` | `/data/images/<item_id>/001.jpg` |
| `source_url` | Where it came from |
| `sha256` | So an identical image is never downloaded or uploaded twice |
| `width`, `height`, `bytes` | |
| `platform_ids` | The id each platform gave the uploaded copy |

Originals are kept at full resolution. Platform-sized copies are generated on
demand and are disposable.

### 2.6 `order` — one per sale

| Column | Notes |
|---|---|
| `order_id`, `platform`, `platform_order_ref` | |
| `item_id` | |
| `sold_price`, `postage_charged`, `postage_cost`, `platform_fees`, `net_received` | All in pence. Blank if the platform does not say — never estimated |
| `buyer_name`, `buyer_username` | Personal data — see §6 |
| `delivery_address` | Personal data |
| `sold_at`, `posted_at`, `delivered_at`, `completed_at` | |
| `carrier`, `tracking_number`, `tracking_status`, `last_tracking_check` | |
| `parcel_photo_image_id` | The photo of it in its bag |
| `status` | `sold` · `awaiting_post` · `posted` · `in_transit` · `delivered` · `completed` · `issue` |

### 2.7 `message` — buyer/seller communications

| Column | Notes |
|---|---|
| `order_id` or `item_id` | |
| `platform`, `direction`, `sent_at`, `author`, `body`, `attachments` | A copy, kept with the sale, as you asked |

### 2.8 `purchase` and `lot` — the money in

| Column | Notes |
|---|---|
| `purchase_id`, `date`, `source`, `total_cost`, `notes` | Typed by hand — no platform provides this |
| `lot_id`, `lot_cost`, `item_count`, `apportionment_method` | **Job lots are the normal case, not the exception** — the real ledger shows 8,196 items bought for £2,234.35, about £0.27 each. Per-item cost is always derived |
| `trip_id`, `date`, `trips`, `litres_per_trip`, `price_per_litre` | **Posting trips and petrol.** Already in the existing books as `trips × 0.959 × price per litre`, and part of how profit is worked out. See `EXISTING_LEDGER.md §3` |

### 2.9 `event` — the audit trail

Every change: what, when, by whom (you, or the system), before and after. This is
what makes undo possible and what answers "why did that price change?".

## 3. The status lifecycle

```
draft ──► needs_info ──► on_sale ──► sold ──► posted ──► delivered ──► completed ──► archived
                            │                                              │
                            └──► removed (withdrawn, lost, damaged)        └──► issue (late, dispute, return)
```

**Nothing is ever deleted, and nothing is ever moved between files.** The status
changes; the exporter decides which CSV a row appears in. That is what makes
"cut from on-sale into sold" safe.

## 4. The four CSVs

Exported on demand and on a schedule, from the database.

### 4.1 `onsale_inventory.csv` — everything currently for sale

`item_id`, `storage_code`, `title`, `description`, `brand`,
`size_uk`, `size_eu`, `size_us`, `size_letter`, `size_other`,
`measurements` (`chest=46cm;length=98cm`),
`colour_primary`, `colours_all`, `material`, `condition`,
`categories_vinted`, `categories_ebay`, `categories_shopify`,
`price`, `currency`, `cost`,
`date_added`, `date_listed`,
`listed_vinted`, `listed_ebay`, `listed_shopify`,
`url_vinted`, `url_ebay`, `url_shopify`,
`image_count`, `image_folder`, `missing_fields`, `notes`

### 4.2 `sold_items.csv` — the two sections you described

**Section 1, the item:** every column above, frozen as it was when it sold.
**Section 2, the sale:** `sold_at`, `platform`, `sold_price`, `postage_charged`,
`postage_cost`, `fees`, `net_received`, `profit`, `buyer_username`, `carrier`,
`tracking_number`, `posted_at`, `parcel_photo`, `message_count`,
`messages_file`.

Messages go in a per-order text file referenced by `messages_file`, because a
conversation inside a spreadsheet cell is unreadable. (Or inline, if you would
rather — Q33.)

### 4.3 `orders.csv` — the short note per sale

`order_ref`, `date`, `platform`, `item_id`, `storage_code`, `title`,
`sold_price`, `net_received`, `status`, `tracking_number`, `days_to_deliver`.

### 4.4 `archive.csv` — completed, kept 5 years

Everything from `sold_items.csv` plus `completed_at`, `delivered_at`,
`total_days`, and any issue notes.

## 5. Flattening rules — how multiple values survive a CSV

A spreadsheet has one box per cell, so multi-value data has to be flattened
predictably:

1. **Known systems get their own column** — `size_uk`, `size_eu`, `size_us`,
   `size_letter`. Predictable, sortable, filterable.
2. **Anything else goes in a catch-all** — `size_other`, semicolon-separated.
3. **Lists use `;`** — `colours_all = Navy;White`.
4. **Key/value lists use `key=value;`** — `measurements = chest=46cm;length=98cm`.
5. **Never a comma inside a value.** It survives quoting, but not the first
   person who opens the file in something careless.
6. **Import reverses all of the above**, so a CSV edited by hand can be read back
   in. That is what makes hand-editing safe.

## 6. Retention and personal data

- Financial records for 5 years is normal for UK self-employment, and that is
  what `archive.csv` is for.
- **Buyer names, addresses and message histories are a different thing.** They
  are personal data, and "keep everything forever" is not automatically the right
  answer. A sensible default: keep the financial record for 5 years, and trim
  addresses and message bodies after a shorter period once returns and disputes
  are closed.
- Nothing here is legal advice. It is worth deciding deliberately rather than by
  accident — Q30.

## 7. Where identity lives

- **The SKU is identity**, and the business already treats it that way. It is
  never recycled, so it survives a sale and return: same number, same box, same
  listing re-uploaded.
- **`item_id` is a surrogate** — a UUID the database uses internally and nobody
  ever sees. It exists so a deliberate re-box can change the SKU without
  orphaning five years of history, not because the SKU is unreliable.
- The SKU stays at the end of every listing description, because that is how the
  system recognises a listing it has never seen before.

### Returns

A return is not a new item:

1. The order moves to `returned`; the money and the history stay against it.
2. The item goes back to `on_sale` **with its original SKU**.
3. The stored listing content is re-published unchanged — no retyping.
4. The garment goes back in the same box, in the same numbered slot.

That is only possible because the number was never given to anything else.
