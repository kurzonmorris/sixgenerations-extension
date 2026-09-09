# Ledger Design — purchases and sales

The spreadsheet side: what a garment cost, what it sold for, where, and what was
left.

> **Read `docs/EXISTING_LEDGER.md` first.** The real books arrived on 2026-09-09
> — five years, 2,864 sales, £11,010.77 — and they answer several of the
> questions this file was written to ask. In particular: **job lots are the
> normal case**, **petrol is already part of the profit formula**, and **nothing
> in the current ledger can be joined to a listing** because there is no SKU on a
> sale. The design below stands, with those three facts moved from "proposed" to
> "required".

---

## 1. What it is for

Three questions, in order of how often they get asked:

1. **Did this garment make money?** Cost → sale price → fees and postage → net.
2. **What is still in the boxes, and what did it cost?** Unsold stock value.
3. **What did the business do this month/quarter/year?** Totals for bookkeeping.

Anything that does not serve one of those three is out of scope.

## 2. Two sheets, one key

The pairing key is the same storage code used everywhere else — `13-8 24`. It is
what joins a purchase to its listings and to its eventual sale.

### Sheet 1 — Purchases (one row per garment, entered by hand)

| Column | Example | Source |
|---|---|---|
| Storage code | `13-8 24` | Typed once, when the item is boxed |
| Date bought | `2026-04-12` | Typed |
| Bought from | `Car boot, Newark` | Typed |
| Cost | `2.50` | Typed |
| Lot / job-lot reference | `Lot 8` | Typed, optional — see §5 |
| Description | `Navy wool coat, M&S, 14` | Typed, or pulled from the listing once it exists |
| Listed on | `Vinted, eBay` | **Filled in by the extension** |

### Sheet 2 — Sales (one row per sale, written by the extension)

| Column | Example | Source |
|---|---|---|
| Storage code | `13-8 24` | Matched from the listing description |
| Date sold | `2026-09-01` | Platform |
| Platform | `Vinted` | Platform |
| Sold price | `18.00` | Platform |
| Postage charged | `3.29` | Platform |
| Postage cost | `2.95` | Platform where available, else typed |
| Platform fees | `?` | Platform — availability differs, see §4 |
| Net received | `18.00` | Calculated |
| Cost | `2.50` | Looked up from Purchases |
| **Profit** | `15.50` | Calculated |
| Order reference | | Platform, for tracing a row back |

Everything the extension can fill, it fills. Everything it cannot is left blank
rather than guessed — a wrong number is worse than a missing one.

## 3. Where the sheet lives — the real decision (Q19)

| Option | How | Good | Bad |
|---|---|---|---|
| **A. Google Sheets** | `chrome.identity` + Sheets API. Client ID in the manifest, **no client secret needed** in an extension | Live, on any device, familiar, shareable, formulas already work | Needs a Google account connected and a Cloud project set up once |
| **B. Local file** | Extension writes `.csv` / `.xlsx` to Downloads; opened in Excel or LibreOffice | No account, no cloud, nothing to set up. Fits "no third party" | One-way. Hand-typed purchases live in a file the extension can only append to, not read reliably |
| **C. Inside the extension** | A table in `chrome.storage.local`, with export | Simplest, works offline, nothing to connect | It is a spreadsheet re-implemented badly, and one machine holds the only copy |
| **D. B + C** | Extension holds the data, exports on demand | Keeps the interface simple and still gives a real spreadsheet | Two copies that can drift |

**Recommendation if no answer comes: A.** It is the only option where purchases
can be typed on a phone at a car boot sale and read by the extension the same
day, and the extension-side OAuth is genuinely simple. It also keeps the ledger
out of the extension's own interface, which suits `INTERFACE_PRINCIPLES.md`.

*Nothing has been built either way — this is deliberately still open.*

## 4. What each platform actually gives us

| Platform | Sales data | Fees | Confidence |
|---|---|---|---|
| **Shopify** | Admin GraphQL `orders` — line items, totals, dates. Clean | Payment processing fees are on the order's transactions | **High.** Documented API, already connected |
| **eBay** | Sell Fulfillment API `getOrders`, or the sold-items page | Final value fee is per-order and available in the API | **Medium.** Depends on Q15 — API access vs reading the page |
| **Vinted** | The sold section of the wardrobe, read the same way as everything else | **Unknown.** UK private sellers pay no selling fee, business/Pro accounts do. Which applies here is Q22 | **Low.** No API, no documented fee breakdown, and the page may not show one |

**So the fee column will be complete for Shopify, probably complete for eBay, and
possibly always blank for Vinted.** That is worth knowing before designing around
it.

## 5. Job lots — the thing that breaks naive cost tracking

Second-hand clothing is often bought as a bundle: £40 for a bin bag of 30
garments. There is no per-item price, so "cost" has to be apportioned.

| Method | Description |
|---|---|
| Even split | £40 ÷ 30 = £1.33 each. Simple, defensible, usually what small resellers do |
| By expected value | Weight the coat higher than the t-shirt. More accurate, needs a judgement per item |
| Lot-level only | Track the lot's cost and the lot's total sales; no per-item profit |

→ **Q21.** This changes the shape of the Purchases sheet, so it is worth
answering before anything is built.

## 6. What it must not do

- **No accounting claims.** This is a record, not a tax return. It does not do
  VAT, it does not do HMRC self-assessment, and it must not imply it does.
- **No guessed numbers.** Blank beats wrong.
- **No fee estimates.** If the platform does not give the fee, the cell is empty.
- **No sales invented from a listing disappearing.** A listing that vanishes is
  not proof of a sale — it may have been deleted or ended. Only a confirmed sale
  writes a row. → **Q23**
