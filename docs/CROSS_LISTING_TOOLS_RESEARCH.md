# Cross-Listing Tools — what already exists, and what to take from it

Researched September 2026. The point of this file is to avoid re-inventing badly
what a dozen paid tools have already worked out, and to be clear about where this
project deliberately goes the other way.

Sources are at the bottom. **Nothing here was tested** — it is documentation and
comparison reading, not hands-on use.

---

## 1. The field

| Tool | Shape | Marketplaces | Vinted? | Shopify? |
|---|---|---|---|---|
| **Vendoo** | Chrome extension + web app + phone app | eBay, Poshmark, Mercari, Depop, Etsy, Facebook, Grailed, Shopify, Whatnot, Vestiaire | **Advertised, then quietly dropped.** Users report it disappears after subscribing | Yes |
| **List Perfectly** | Extension + web app | Similar list | Partial / unreliable reports | Yes |
| **Crosslist** | Web app + extension | Similar list, EU-leaning | Claims yes | Yes |
| **PrimeLister** | Chrome extension, started as Poshmark automation | eBay, Poshmark, Mercari, Depop, Grailed, Etsy, Shopify | No | Yes |
| **Flyp / Voolist / Flipsail** | Newer, cloud-first | eBay-centric | No | Varies |

**The finding that matters: no mainstream tool reliably does Vinted.** Vinted has
no public seller API and actively blocks automation (`PROJECT_INFO.md §2.4`), so
the commercial tools either dropped it or never had it. That is the entire reason
this project exists rather than a £30/month subscription.

## 2. The two architectures

**Form-fillers (extension-driven).** The extension opens a tab on the
marketplace, fills the listing form as the signed-in user, and clicks. List
Perfectly and PrimeLister's crosslisting work this way, and they are criticised
for being slow, needing the browser open, needing manual confirmation, and
filling only some fields.

**Cloud (API-driven).** The vendor holds an OAuth connection per marketplace and
does everything server-side. Faster, works with the computer off, but needs an
account with the vendor, needs a public API on the marketplace, and cannot touch
Vinted at all.

**What this project is:** a hybrid, and the split follows what each platform
actually offers.

| Platform | Approach | Why |
|---|---|---|
| Shopify | API (Admin GraphQL) from the service worker | A real, documented API with a proper token |
| Vinted | Tab-driven, as the signed-in user | No API. Form-filling is the only honest route |
| eBay | **Undecided — Q15.** eBay has a real API, but the OAuth exchange needs a client secret an extension cannot safely hold (`PROJECT_INFO.md §3.2`) | This is the one genuine fork in the road |

## 3. What is worth copying

1. **A dry run / preview before anything is written.** The tools that skip this
   have the worst reviews. Already the default here.
2. **One inventory record, many listings.** Every tool models the item once and
   treats each marketplace listing as a projection of it. `garmentItem.js`
   already does this — eBay becomes a third projection, not a third code path.
3. **Delist-when-sold as the headline feature.** Across every comparison
   article this is the feature people actually pay for; double-selling a
   one-of-a-kind garment costs a refund, postage and a rating. This is X-02 in
   `FEATURE_SPECIFICATION.md` and it should be the goal of everything before it.
4. **Templates for the boring fields.** Postage, returns, and condition wording
   are the same on almost every garment. eBay in particular requires business
   policies before a listing can publish.
5. **A sales and profit view.** Vendoo and List Perfectly both bolt on a
   ledger — because resellers ask for it constantly. Here it is `LEDGER_DESIGN.md`.

## 4. What is worth avoiding

1. **Marketplace count as a selling point.** Vendoo caps each listing at three
   marketplaces; the number in the marketing is not the number you get. Three
   platforms done properly beats ten done half-way.
2. **Busy dashboards.** Every one of these tools opens on a wall of tiles,
   badges, counters and upsells. That is precisely the thing this build must not
   do — see `INTERFACE_PRINCIPLES.md`.
3. **Half-filled listings.** The complaint levelled at the form-fillers is that
   they fill some fields and leave the rest. Better to write fewer fields and say
   clearly which ones were left alone.
4. **A subscription and an account.** Nothing here should require signing in to a
   third party or trusting anyone else with a Shopify token.
5. **Silent failure.** If a write fails, the platform's own error message goes in
   the log, verbatim. Already the rule in `syncRunner.js`.

## 5. The one honest advantage the paid tools have

They run in the cloud, so delisting happens whether the computer is on or not. A
browser extension only acts while Chrome is open on that machine. At 2000 items
selling across three platforms, **that gap is real** — a garment can sell on
Vinted at 2am and stay live on eBay until the browser is next opened.

Options if that becomes a problem, none of them small:
- Accept it, and run the sync at a fixed time each day.
- Leave Chrome running on the Unraid Windows VM with the extension scheduled.
- Move the eBay half to a small service on Unraid (the eBay API allows this;
  Vinted does not).

→ **Q18.**

---

## Sources

- [Best 10 Cross Listing Apps in 2026 — Crosslist](https://crosslist.com/blog/best-crosslisting-apps-for-resellers)
- [Best Cross Listing Apps For Resellers in 2026 — Vendoo blog](https://blog.vendoo.co/crosslisting-software-for-online-resellers)
- [Vendoo Crosslist Extension v3 — Chrome Web Store](https://chromewebstore.google.com/detail/vendoo-crosslist-extensio/mnampbajndaipakjhcbbaihllmghlcdf)
- [Vendoo vs List Perfectly vs Crosslist](https://crosslist.com/blog/vendoo-vs-list-perfectly)
- [PrimeLister vs Vendoo](https://crosslist.com/blog/primelister-vs-vendoo)
- [List Perfectly vs Crosslist vs Vendoo — Tech For Good](https://www.techforgood.net/guestposts/list-perfectly-vs-crosslist-vs-vendoo-which-multi-listing-tool-is-best-for-online-sellers)
- [5 Best Cross-Listing Apps 2026 — Voolist](https://www.voolist.com/blog/best-cross-listing-apps-2026)
- [Cross-Listing Tools Comparison 2026 — Flipsail](https://www.flipsail.io/blog/best-cross-listing-tools-2026)
