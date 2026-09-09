# The existing ledger — `six_generations_2.xlsx`

The real book of the business, read on 2026-09-09. **Five years of trading is in
this file**, and the new system has to earn its place against it, not ignore it.

Nothing here is a criticism of the sheet. It has done the job for five years,
which is more than most systems manage.

---

## 1. What it is

| | |
|---|---|
| **Shape** | One sheet per month — 63 of them, from **October 2021** to **September 2026**, plus `template`, `Ava sales` and `James toys` |
| **Sales recorded** | **2,864** |
| **Total sold** | **£11,010.77** — an average of **£3.84** a sale |
| **Items bought** | **8,196**, for **£2,234.35** — an average of **£0.27** an item |
| **Bought but not yet sold** | **≈5,332** |

By year:

| Year | Sales | Value |
|---|---|---|
| 2021–22 | 466 | £1,806.33 |
| 2022 | 372 | £1,600.67 |
| 2023 | 625 | £2,101.35 |
| 2024 | 411 | £1,384.75 |
| 2025 | 596 | £2,261.28 |
| 2026 (to Sept) | 348 | £1,464.32 |
| `Ava sales` / `James toys` | 46 | £392.07 |

## 2. The columns

Three header rows, then data in rows 4–81, then a totals block at rows 82–83.

| Col | Header | Filled | Notes |
|---|---|---|---|
| A | **No of Items** (bought) | 313 | A job-lot count — 140 items in one go |
| B | Bought Date | 182 | Text, `d.m.yy` |
| C | **Bought Amount** | 311 | The whole lot's price |
| D | *(spacer)* | — | |
| E | **Name** | 2,864 | Free text: "aubergine coat", "phonics game" |
| F | Sold Date | 2,859 | Text, `d.m.yy` |
| G | **Sold Amount** | 3,008 | |
| H | Post Date | **1,759 (61%)** | |
| I | Tracking no. | **16 (1%)** | Barely used |
| J | Times Posted | 164 | Trips to the post office, for petrol |
| K | *(spacer / petrol rate)* | 126 | £1.40 per litre in recent months |
| L | Withdrawal | 3 | Money taken out of the platform balance |

## 3. The totals block, and the thing I did not expect

Row 82 holds labels, row 83 the formulas:

```
A83 = SUM(A4:A81)              items bought this month
C83 = SUM(C4:C81)              spent on stock
G83 = SUM(G4:G81)              sold
J83 = SUM(J4:J81)              posting trips
I83 = J83 * (0.959 * K83)      petrol cost  =  trips × litres × price per litre
E83 = G83 - (C83 + I83)        PROFIT  =  sold − (stock + petrol)
```

**Petrol is already part of how profit is worked out.** That was D-149 in the
feature list — "mileage and expenses" — sitting unticked in the unanswered
section, when it is in fact already load-bearing. The new system must carry it,
and carry it the same way: trips counted, a rate per litre that can be changed,
and profit that includes it.

## 4. What this proves about the business

Four things the sheet says plainly, all of which change the design:

**4.1 Job lots are the normal case, not an edge case.** 8,196 items for £2,234
means stock arrives in bags and boxes, not one at a time. Per-item cost is an
apportionment, always. `DATA_MODEL.md §2.8` was right to have a `lot` table; it
should be the primary way a purchase is recorded, and per-item cost is derived.

**4.2 There is a large unlisted backlog.** Roughly **5,332 items bought and not
yet sold**, against about 2,000 currently on Vinted. So there are on the order of
**3,000 items bought and never listed**. That is what "the table" queue is for,
and it is the single biggest lever on income in the whole system — every one of
those is stock already paid for.

**4.3 Postage is recorded loosely and tracking barely at all.** A post date on
61% of sales and a tracking number on 1%. That is not a criticism — typing 16
digits into a spreadsheet by hand is miserable. It is exactly the kind of thing
the system should capture without anyone typing it, and it is why D-108 to D-110
matter.

**4.4 Nothing in the ledger can be joined to a listing.** Sales are identified by
a free-text name. There is no SKU column, no item id, no link back to Vinted. So
the current sheet can tell you *how much* was made, but never *which garment*,
what it cost, how long it sat, or which platform did better. **Putting the SKU on
the sale record is the single change that unlocks everything the analysis
features promise.**

## 5. Traps in the data, for whoever writes the import

- **Dates are text, not dates.** `7.9.26` stored as a string, and — worse — some
  cells carry a `mm-dd-yy` number format over text that is actually `d.m.yy`.
  Read them as day-first, and do not trust the cell format.
- **`Jamuary 2025`** is a typo in a sheet name. Match month names loosely.
- **The first eight sheets have no year** (`October` … `May`). They are
  2021–2022, in order.
- **Totals rows sit inside the data range.** Row 82/83 have text in the Name
  column; an import that does not skip them will invent phantom sales and double
  the month's takings. (It caught me on the first pass.)
- **`Ava sales` and `James toys`** are separate streams. Are they a different
  seller, a different category, or someone else's stock? → Q38.
- **Rows are capped at 81** per sheet, so a busy month has nowhere to go.

## 6. What the new system does with it

| Step | What happens |
|---|---|
| **1. Import it whole** | All 2,864 sales, all 63 sheets, into the `order` and `purchase` tables. Five years of history is worth keeping |
| **2. Keep the name** | Free-text names stay as `legacy_name`. Where a name matches a known item, link it; where it does not, the row still stands on its own |
| **3. Keep the petrol** | Trips, rate, and profit-including-petrol, exactly as the formula does it |
| **4. Recreate the monthly view** | An export that looks like the sheet, month by month, with the same totals — so nothing is lost by moving |
| **5. Then improve it** | SKU on every new sale, tracking captured automatically, fees recorded, cost per item derived from the lot |

**The monthly sheet keeps working until the replacement is demonstrably better.**
Nobody should have to trust a new system with five years of accounts on day one.

## 7. Questions this raised

- **Q38** — what are `Ava sales` and `James toys`?
- **Q39** — import all five years, or start clean and keep the file for history?
- **Q40** — is `0.959` litres per posting trip still right, and is £1.40 the
  current price per litre?
- **Q41** — roughly 3,000 items bought and never listed. Is that right, and is
  clearing it a priority for the system?
