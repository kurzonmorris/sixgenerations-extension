# The Crosslist export — `listings-2026-09-15.csv`

Read 2026-09-15. **2,125 items, 39 columns.** This is the file the whole
inventory comes from, so what is in it — and what is not — decides what the
importer has to do.

Nothing here is a criticism. Five years of listings typed by hand, at 3–6 a day,
will always look like this.

---

## 1. The numbers

| | |
|---|---|
| Items | **2,125** |
| **Listed at some point** (`LastListedOn` set) | **1,137** (53.5%) |
| **Never listed anywhere** | **988** (46.5%) |
| Recorded as sold | 109 · 16 of them sold without ever being listed |
| Photos | **9,098** — 1 to 15 an item, 4.3 on average |
| With a usable box code | 1,720 (80.9%) |
| **With no code at all** | **405** (19.1%) |
| **Sharing a code with another item** | **639 rows across 315 codes** |

**988 never listed** is the backlog, and it matches what you said almost exactly.

## 2. Three things hidden in the description

The description is not just prose. It ends with two structured lines that no
column holds:

```
High waisted black bikini bottoms, size labelled UK22.

W65g
B8-3 36
```

| | Meaning | Coverage |
|---|---|---|
| `W65g` | **The weight in grams** | **2,069 rows (97.4%)** |
| `B8-3 36` | The SKU, with a `B` prefix | 1,720 rows (80.9%) |

**The weight matters.** The `ShippingWeight` column is useless — it holds 16.00
on 847 rows, 500.00 on 761 and 1000.00 on 98, which are defaults nobody set. The
real weight is in the text, on nearly every item, and postage depends on it.
The importer reads it from there.

**The `B` prefix is new to us.** Everything discussed before was `13-8 24`; every
code in this file is `B13-8 24`. Presumably "box". The parser already tolerates
it, but it is worth knowing it is there — see Q48.

## 2A. Answered 2026-09-15

| Question | Answer |
|---|---|
| The `B` prefix | **Just "box".** Technically irrelevant, kept for continuity. The raw code is stored verbatim in `legacyCode`; the normalised one ignores it |
| Shared codes | **Codes were reused occasionally**, almost always because an item was **returned and relisted**. Hence the requirement for a dated history against every item |
| Items with no code | **Not a mistake.** Jackets, toys and books that do not fit a normal box. Being rectified slowly. A real state, so they import and are flagged |
| **Why 988 items are offline** | **Vinted changed how sizes are displayed last year**, so almost the whole catalogue was taken down to be corrected by hand. It has not gone back up. **That is the backlog** — not items never listed, but items *delisted pending a size fix* |

**The last one changes what this project is for.** The 988 are not unlisted
stock, they are *withdrawn* stock: photographed, described, priced, and earning
nothing while they wait for someone to check a size. Getting them back up is the
first thing the system exists to do.

## 3. Duplicate titles — a correction

**What was written here on 2026-09-15 was too confident.** The claim was that
duplicate-title pairs are separate garments because "not one of 468 pairs shares
a photograph". That compared **URLs, not images**. Crosslist copies images when a
listing is duplicated, which produces different URLs for identical photographs —
so the test proved nothing.

The worked example still stands on its own (creation dates six months apart, one
sold and one not), and the returned-and-relisted explanation fits it exactly. But
**some of those pairs are very probably the same physical garment listed twice.**

**This is now answerable rather than arguable.** Every photo is hashed as it is
downloaded, and `duplicateImages()` in `core/photoStore.py` lists the photographs
held against more than one item. Run it once the fetch has finished and the
question is settled by content.

## 3B. The original note, kept

514 titles appear more than once, covering 1,127 rows. That looked like the
export listing an item once per marketplace. **It is not.** A worked example:

```
Black t-shirt   created 2025-09-30   listed 2026-03-16   SOLD 2026-03-16   qty 0
Black t-shirt   created 2026-03-10   listed 2026-03-16   not sold          qty 1
```

Different creation dates six months apart, and **not one of the 468 duplicate
pairs shares a photo** — every row has its own photographs. These are separate
physical garments that happen to be the same kind of thing, which is exactly what
second-hand clothing looks like.

**So one row is one item.** That is the simplest possible answer and it makes the
importer straightforward.

## 4. The two problems that need you

### 4.1 Four hundred and five items with no code

Where they end instead:

| Ends with | Rows | Looks like |
|---|---|---|
| The weight, `W490g` | 269 | The code was never added |
| A bare `B` | 38 | Someone started typing it and stopped |
| A bare `W` | 16 | Same, for the weight |
| `C01`, `M02`, `PP01` | 20 | **A different scheme entirely** — the titles are all toys (Chase, Marshall, Paw Patrol) |
| `B2-1` | 8 | Column and box, no item number |
| `B1-1 05A` | 2 | A letter on the end of the item number |
| Prose | ~50 | Books, mostly Dan Dare — no code at all |

**A code appears nowhere else in those descriptions** — it is not misplaced, it
is absent. These items cannot be found in the room from the data alone.

### 4.2 Six hundred and thirty-nine items sharing a code

315 codes are used by more than one item. Only 30 of those are explained by one
having sold and the slot being reused. **285 clashes have two or more unsold
items claiming the same place**, like this:

```
11-1-26   Black joggers size S          created 2026-04-21   never listed
11-1-26   Black triangle brief UK12 L   created 2026-03-10   listed
11-1-26   Black triangle brief UK12 L   created 2025-09-19   SOLD
```

The sold one explains itself. The other two are a genuine collision: two garments
in one slot, and no way to tell which is which from the file.

This is the opposite of what a permanent, never-recycled SKU is meant to be, so
it needs deciding rather than guessing — Q49.

## 5. What the columns actually give us

**Useful and full:** `Title`, `Description`, `Price`, `CategoryLabel` (a full
path — *"Clothing, shoes & accessories > Womenswear > Women's dresses"*),
`Condition`, `Quantity`, `Created`, `Photos`.

**Useful, partly filled:** `Brand` (81.9%), `SizeLabel` (80.0%), `Color`
(91.8%), `Color2` (46.2% — **the second colour the data model already expects**),
`LastListedOn` (53.5%), `Sold` (5.1%).

**Empty in every row**, so nothing is lost by ignoring them: `OriginalPrice`,
`CostOfGoods`, `DomesticShippingPrice`, `WorldwideShippingPrice`,
`FreeDomesticShipping`, `FreeWorldwideShipping`, `SmartPricingPrice`,
`AuctionStartingPrice`, `InternalNote`, `Labels`.

**Nearly empty:** `SKU` (14.6%, and it does **not** hold the box code),
`WhoMade`/`WhenMade` (11.8%), `Tags` (1 row), the shipping dimensions (1 row).

**Missing entirely: where an item is listed.** `LastListedOn` says *when*, never
*which marketplace*. That is survivable — see §6.

## 6. Where an item is listed has to come from the platforms

A CSV cannot answer this and should not be asked to: listings change daily, and
a file is out of date the moment it is written.

- **The export** is the source of truth for what the garment *is*.
- **Vinted** is the source of truth for what is live on Vinted — and the existing
  extension already reads the whole wardrobe. Matching it against the import on
  the SKU answers the question properly, today.
- eBay and Shopify answer for themselves later.

So `LastListedOn` is imported as what it is — *"this was listed at some point"* —
and never treated as *"this is live now"*.

## 7. The photos are on a clock

**All 9,098 photos are hosted on `media-na.crosslist.com`.** Not on Vinted, not
on eBay — on the tool being paid for. The day that subscription ends, every one
of those URLs is likely to stop resolving, and with it the only copy of the
photographs for **988 items that have never been listed anywhere**.

**Downloading them is the most time-critical thing in this project.** It needs no
decisions, breaks nothing, and is worth doing before anything else in stage 3.

## 8. What the importer will do

1. One row → one item. `Id` is kept as `crosslistId` so a second run updates
   rather than duplicates.
2. Read the SKU from the end of the description, `B` prefix and all.
3. Read the weight from `W###g` and put it in `weightGrams`, where postage needs it.
4. `Color` and `Color2` become two colour attributes, primary and secondary.
5. `CategoryLabel` becomes a category path against platform `crosslist`.
6. `Sold` set → `status = sold`. Everything else → `needs_info`, unverified.
   **Nothing is imported as `on_sale`** — that is decided by reading Vinted.
7. Download all 9,098 photos, numbered in their original order, deduplicated by
   content.
8. **Items with no code and items sharing a code are imported and flagged**, not
   skipped and not merged. They become the first thing the review queue shows.
9. Dry run first, always: what it would create, change and skip, before anything
   is written.
