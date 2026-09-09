# Tasks for the Claude browser extension

You offered to run things in the browser and send back what they find. These are
the jobs worth doing, each as a **prompt you can paste straight in**, in the
order that unblocks the most work.

**How to use one:** open the page named at the top of the task, start Claude in
the browser, paste the prompt, then paste the answer back to me (or save it to a
file in the repo). Everything that comes back gets written into
`EXPLAINED_six-generations_Extension.md`.

**A rule for all of these:** they only ever look at **your own account and your
own data**, on pages you are signed into. Nothing asks for anyone else's
listings, and nothing asks for another company's source code.

---

# Priority 1 — the three that unblock the most

## Task 1 — Vinted: what is actually in an item

**Open:** one of your own Vinted listings, then its **edit** page.

> I am on my own Vinted listing edit page. Please list every single field this
> form contains, in the order they appear. For each field give me: the label as
> shown, whether it is free text / a dropdown / a picker / multi-select, whether
> it is required, and the exact options if it is a fixed list. I especially need
> the details of: every size option and whether more than one size system is
> shown, the colour picker and whether more than one colour can be chosen, the
> category picker and its full path for this item, condition, brand, material,
> parcel size, and any measurement fields. Then open the browser's network tab,
> reload, and tell me which URL the page loads the item's data from and paste the
> full JSON response for this one item with nothing removed except anything that
> looks like a token or session id. I want to see every field name in that JSON,
> including ones the form does not show.

**Why:** the current reader only takes a dozen fields. This tells us everything
that exists, which is the basis of the whole data model.

## Task 2 — Vinted: is this a business account, and does the official API apply?

**Open:** your Vinted account settings, then <https://pro-docs.svc.vinted.com/>

> Two things. First, on my Vinted account settings page, tell me whether this
> account is a private account or a business/Pro account, and quote whatever
> wording the page uses. Tell me whether there is any option to convert to a
> business account and what it says the consequences are, especially anything
> about selling fees. Second, on the Vinted Pro Integrations documentation site,
> summarise: what the Items API, Orders API and Webhooks API can each do, exactly
> how a seller applies for access, whether approval is manual, whether there is a
> limit on the number of active items, and whether there is any cost. Quote the
> limits verbatim.

**Why:** if this account is or can be a business account, an official supported
API replaces the fragile browser scraping, and orders and notifications come for
free. It is the single biggest fork in the road.

## Task 3 — Crosslist: get your data out, and copy the good bits of its table

**Open:** your Crosslist account.

> This is my own account with my own listings in it. First, find the export or
> download feature and export all of my listings to CSV — tell me where the
> option is and what formats it offers. Then tell me exactly which columns the
> export contains, with two example rows (you can blank out anything personal).
> Then, from the listing edit screen, list every field Crosslist stores about an
> item, and for each one say which marketplaces it maps that field to. Then open
> the inventory table — the screen that lists everything it holds — and describe
> it in detail: which columns it shows, what the search box searches, what
> filters exist, whether rows can be edited in place, and how it handles
> thousands of items (paging, scrolling, how long it takes). Finally
> describe, as a user would see it, what happens when an item sells on one
> marketplace — what it does on the others, how quickly, and whether it needs my
> browser open. I am documenting what I would lose if I cancelled the
> subscription, and what I already have that I can import elsewhere.

**Why:** that export is your own data and the fastest possible way to load the
new system — no scraping needed for the initial 2,000 items. It also tells us
exactly which fields a working cross-lister keeps, and what "cancel day" would
cost you.

---

# Priority 2 — needed before eBay work starts

## Task 4 — eBay: what a clothing listing actually demands

**Open:** eBay's "Sell an item" form, part-filled for a women's dress, on
`ebay.co.uk`.

> I am on eBay's sell form for a women's dress. List every field on this form in
> order: the label, whether it is required or optional, and the exact options for
> anything that is a fixed list. Pay particular attention to the "item specifics"
> section — tell me which specifics eBay marks as required for this category,
> which as recommended, and give me the exact allowed values for size, size type,
> colour, style, material, and department. Tell me the full category path this
> form has selected and whether eBay shows a numeric category id anywhere. Then
> tell me what eBay says about business policies for postage, returns and
> payment — whether they are required, and where they are managed.

## Task 5 — eBay: what my existing listings look like

**Open:** your eBay active listings, in the seller hub.

> These are my own eBay listings. Tell me roughly how many active listings there
> are. Then open three of them and tell me, for each: whether there is anything
> in the custom label / SKU field and what it is, and whether the description
> ends with a code in the form "13-8 24" (three numbers, two separated by a dash
> and the third after a space). If neither is present, say so plainly. Also tell
> me whether the seller hub offers a bulk CSV download of my listings, and where.

**Why:** this answers whether eBay listings already carry the storage code, which
decides whether eBay can be matched at all without a manual back-fill.

## Task 6 — eBay: the developer terms, read properly

**Open:** <https://developer.ebay.com/api-docs/static/oauth-auth-code-grant-request.html>
and <https://developer.ebay.com/develop/get-started/api-call-limits>

> Summarise these two pages precisely. From the first: the exact token endpoint
> URL, the required headers, what redirect_uri must be set to, and the stated
> lifetimes of the user access token and the refresh token. Tell me explicitly
> whether eBay supports PKCE or any flow that does not require a client secret.
> From the second: the default daily call limits for each API, and whether the
> limit is per application or per user. Quote the numbers.

**Why:** I could not reach eBay's developer site from where I run — those pages
are blocked here. Everything in `docs/PROJECT_INFO.md §3` is currently from
secondary sources and marked unverified.

---

# Priority 3 — filling in the picture

## Task 7 — Shopify: what the store already uses

**Open:** your Shopify admin, on a product.

> This is my own Shopify store. For this product, list every field that has
> something in it, including the product type, vendor, tags, collections it
> belongs to, all variant options and their values, and any metafields. Then tell
> me: how many products the store has in total, how many collections there are
> and what they are called, and whether the description of this product ends with
> a code in the form "13-8 24". Also tell me which Shopify plan the store is on —
> it is on the billing page — because it sets how fast the API may be used.

## Task 8 — Vinted: what a sale actually looks like

**Open:** one of your completed Vinted sales, and its conversation.

> This is my own completed sale on Vinted. Tell me every piece of information
> shown about it: the sale price, what the buyer paid, postage, any fee shown to
> me as the seller, the dates, the postage method and tracking number, and the
> current delivery status. Tell me exactly where each one appears. Then open the
> conversation with that buyer and tell me how the messages are laid out and
> whether there is a way to see them all at once. Finally, in the network tab,
> tell me which URLs the order page and the conversation page fetch their data
> from.

**Why:** the ledger, the postage tracking and the message copies all depend on
knowing what Vinted will actually give up about a sale, and there is no
documentation for it anywhere.

## Task 9 — Vinted: the category tree

**Open:** the Vinted "list an item" page, on the category picker.

> On the Vinted listing form's category picker, walk through the womenswear
> branch and give me the full tree, level by level, as an indented list. Where
> the page exposes numeric ids in the network tab or the page source, include
> them next to each category name. I need the structure, not every leaf — go
> three levels deep and tell me roughly how many options are at each level.

## Task 10 — can the three sites be shown inside our own page?

**Open:** any page, with the browser's developer tools available.

> For each of `https://www.vinted.co.uk`, `https://www.ebay.co.uk` and
> `https://sixgenerations.co.uk`, tell me the response headers, specifically
> `X-Frame-Options` and any `Content-Security-Policy` containing
> `frame-ancestors`. Then tell me plainly, for each one, whether that site can be
> displayed inside an iframe on a different website. Also check the Shopify admin
> at `admin.shopify.com` separately from the shop's own storefront.

**Why:** the dashboard asks for these three to load inside the web interface.
Marketplaces normally forbid it, and the answer decides between embedding and
opening a tab. See `docs/INTERFACE_LAYOUT.md §6`.

## Task 11 — a sanity check on the interface

**Open:** nothing. This one is for the person who will use the system daily.

> Not a browser task — a conversation. What makes a screen hard to use? Is it
> the amount on it, movement, colour, brightness, the number of choices, or the
> wording? Is there an app or website that feels easy, that we could copy? Light
> or dark? Bigger text? And when you open this tool in the morning, what is the
> one thing you want it to tell you?

**Why:** `docs/INTERFACE_PRINCIPLES.md` is written from general guidance about
designing for autism, ADHD and sensory sensitivity. It is a starting point.
Hers are the rules that actually count.

---

# What to do with the answers

Paste them back and I will:

1. Put confirmed facts into `docs/PROJECT_INFO.md`.
2. Put everything else into `EXPLAINED_six-generations_Extension.md` — used facts
   in the body, not-yet-used ones in the parking lot at §9.
3. Close whichever questions in `docs/OPEN_QUESTIONS.md` the answers settle.
4. Say what became possible that was not before.
