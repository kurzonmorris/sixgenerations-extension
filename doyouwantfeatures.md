# Do you want these features?

**Answered 2026-09-09** (returned as an .odt). This file is now the record of
what was said, not a blank form.

| Mark | Meaning |
|---|---|
| `[x]` | **Yes.** 239 of them |
| `[ ]` | **No.** 13 of them, listed below |

**All 252 are answered.** The missing ticks were never a formatting fault at your
end: the first half was typed in a text editor as literal `[x]` text, and the
second half was done in Google Docs, which turned the brackets into real
checkbox objects. Those objects survive a **markdown** export but are dropped by
.odt, .docx, .pdf and plain text — which is why three exports in a row looked
blank from D-121 on. Read straight from the Google Doc, they were all there.

**The 13 you said no to:**

| | |
|---|---|
| **D-084** | Publish to Shopify as a draft first |
| **D-139** | "Nothing sold in X days" notification *(but D-161, price-drop suggestions in a report, is a yes — a report, not a nag)* |
| **D-173** | One screen, one job. No dashboard |
| **D-174** | Plain sentences, not tables of data |
| **D-226–D-231** | Depop, Etsy, Facebook, Amazon, Whatnot, a second Vinted account *(D-232 is a yes — built so adding one later is one new file)* |
| **D-240** | Print storage-code labels *(D-239, QR-ready, is a yes)* |
| **D-244** | Suggest which items to bundle |
| **D-248** | Free up a storage code when an item is posted |

**D-173 and D-174 settle the interface question.** They were the two rules that
contradicted the dashboard you asked for, and you turned both down deliberately.
Everything else in section 16 stayed ticked. So the design is now unambiguous:
**a dashboard, with tables, that is completely still** — no movement, no hover
effects, muted colours, a word beside every colour, no jargon, detail folded
away.

★ = I would recommend it.

---

## 1. Getting the data out of Vinted

- [x] **D-001** ★ One button that reads the entire wardrobe, every item, every field.
- [x] **D-002** ★ Only fetch what changed since last time, instead of everything.
- [x] **D-003** Read sold items as well as live ones.
- [x] **D-004** ★ Read the full item detail page, not just the summary — more fields live there.
- [x] **D-005** Read draft/unpublished items.
- [x] **D-006** Read hidden/reserved items.
- [x] **D-007** ★ Record the date each item was uploaded.
- [x] **D-008** Record how many views and likes each item has.
- [x] **D-009** Record how long an item has been listed.
- [x] **D-010** ★ Warn when Vinted changes something and the read stops working properly.
- [x] **D-011** Read the whole Vinted category tree once, so categories can be matched later.
- [x] **D-012** Read your Vinted bundles/discounts.
- [x] **D-013** Read offers received on items.
- [x] **D-014** ★ Check whether the account qualifies for Vinted's official business API (would replace most of the above with something supported).

## 2. The detail stored against each item

- [x] **D-015** ★ Multiple sizes per item — UK, EU, US, Italian, letter, all at once.
- [x] **D-016** ★ Actual garment measurements — chest, waist, length, sleeve, shoulder, hem.
- [x] **D-017** Measurements in both cm and inches, converted automatically.
- [x] **D-018** ★ Multiple colours per item, with one marked as the main one.
- [x] **D-019** ★ Multiple categories per item, and a different one per platform.
- [x] **D-020** Material composition as a list — 70% wool, 30% polyester.
- [x] **D-021** ★ Condition in your own words, kept separate from each platform's fixed list.
- [x] **D-022** ★ Flaws recorded individually, each with its own photo.
- [x] **D-023** Style, fit, pattern, neckline, sleeve length, occasion — the fields eBay asks for.
- [x] **D-024** Era / decade, for vintage.
- [x] **D-025** Made-in country.
- [x] **D-026** Care instructions from the label.
- [x] **D-027** ★ Weight and parcel size, for postage.
- [x] **D-028** Original retail price, if known.
- [x] **D-029** ★ A permanent internal id per garment, so re-boxing cannot break anything.
      *You said: we use an SKU system — box column, box, item. e.g. 7-4 21.*
- [x] **D-030** Free-text private notes never shown to a buyer.

## 3. Photos

- [x] **D-031** ★ Download and keep every photo at full resolution.
- [x] **D-032** ★ Keep them numbered in the exact order they were originally set.
- [x] **D-033** ★ Never download or upload the same image twice (matched by content).
- [x] **D-034** Label photos by what they are — main, label, flaw, measurement, parcel.
      *You said: also by the order they are online, and the SKU at the end of the file names.*
- [x] **D-035** Automatically resize per platform, keeping the original untouched.
- [x] **D-036** Reorder photos by dragging, and push the new order everywhere.
- [x] **D-037** Add photos that were never on Vinted.
- [x] **D-038** ★ Photo of the parcel in its bag, attached to the order.
- [x] **D-039** Watermark photos going to some platforms.
- [x] **D-040** Remove or whiten the background automatically.
- [x] **D-041** Straighten and crop automatically.
- [x] **D-042** Warn when an item has fewer photos than a platform wants.

## 4. Where the data lives

- [x] **D-043** ★ A proper database rather than files as the store (CSVs still exported).
- [x] **D-044** ★ Start on SQLite — one file, no admin, copies like any other file.
      *You said: security is also very important, with regular onsite and offsite backups — onsite on the server, offsite on pCloud.*
- [x] **D-045** Postgres instead, from day one.
- [x] **D-046** ★ Everything on the server in Docker, not in the browser.
- [x] **D-047** ★ Survives the move from Unraid to HexOS with no changes.
- [x] **D-048** ★ Nightly automatic backup of database and photos.
- [x] **D-049** Keep a version history of every item, so you can see what changed and when.
- [x] **D-050** ★ Nothing is ever deleted — items change status instead.
- [x] **D-051** Restore-from-backup that you can actually test.
- [x] **D-052** Export everything to a single zip you could hand to an accountant.

## 5. The spreadsheet files

- [x] **D-053** ★ `onsale_inventory.csv` — everything currently for sale.
- [x] **D-054** ★ `sold_items.csv` — the item, the sale, the postage, the messages.
- [x] **D-055** ★ `orders.csv` — a short line per sale.
      *You said: this will be bigger, as it will be used to analyse profit and loss. The current file needs remaking.*
- [x] **D-056** ★ `archive.csv` — completed sales, kept 5 years.
- [x] **D-057** ★ Files rewritten automatically whenever something changes.
- [x] **D-058** Files also written on a schedule, so there is always a recent copy.
- [x] **D-059** ★ Edit a CSV by hand and have the system read the changes back in.
- [x] **D-060** Excel-format (.xlsx) versions as well as CSV.
      *You said: we use LibreOffice, not Microsoft — make it compatible with Calc.*
- [x] **D-061** A Google Sheet that updates itself, so purchases can be typed on a phone.
      *You said: not just updates itself but is also read, to update other systems.*
- [x] **D-062** ★ Multi-value fields flattened predictably — `size_uk`, `size_eu`, and a catch-all.
- [x] **D-063** A separate `purchases.csv` for what things cost.
      *You said: updated in conjunction with the Google Sheet, as that is likely where the user adds purchase information.*

## 6. Putting items on eBay

- [x] **D-064** ★ Create an eBay listing from an item already on Vinted.
- [x] **D-065** ★ Update an eBay price when it changes elsewhere.
- [x] **D-066** ★ End an eBay listing the moment the item sells elsewhere.
- [x] **D-067** ★ Put the storage code in eBay's SKU field, where it is an exact match.
- [x] **D-068** Map Vinted categories to eBay categories automatically.
- [x] **D-069** Fill eBay item specifics (brand, size, colour, style) from what we hold.
- [x] **D-070** ★ Reusable postage / returns / payment policies so every listing does not ask again.
- [x] **D-071** Listing templates per garment type — dresses always described the same way.
- [x] **D-072** eBay-specific pricing — higher than Vinted, because the fees are.
- [x] **D-073** Best-offer settings per item.
- [x] **D-074** Schedule listings to go live at a chosen time.
- [x] **D-075** ★ Read eBay orders and fees back for the accounts.
      *You said: when an item sells on eBay it automatically delists elsewhere. If an item sells at the same time on several sites, tell the user urgently so it can be resolved by hand.*

## 7. Putting items on the Shopify site

- [x] **D-076** ★ Create a Shopify product from an item already on Vinted.
- [x] **D-077** ★ Keep prices in step.
- [x] **D-078** ★ Set stock to zero the moment it sells elsewhere.
- [x] **D-079** Put items into Shopify collections automatically, by category or brand.
- [x] **D-080** Tag products automatically — era, colour, size, condition.
- [x] **D-081** Sizes and colours as proper variant options rather than text.
- [x] **D-082** SEO title and description generated from the item.
- [x] **D-083** ★ Read Shopify orders back for the accounts.
- [ ] **D-084** Publish to Shopify as a draft first, for a look before it goes live.

## 8. Keeping all three in step

- [x] **D-085** ★★ **Sold anywhere → removed everywhere**, automatically. The single most valuable thing here.
- [x] **D-086** ★ One screen showing every item and which platforms it is on.
- [x] **D-087** ★ Warn when the same item sold twice before a check ran.
- [x] **D-088** ★ Decide per field which platform wins — price, stock, description, photos.
- [x] **D-089** Different price per platform, by a rule — eBay +15%, say.
- [x] **D-090** Ask rather than guess when both sides changed since last time.
- [x] **D-091** ★ Undo the last run.
- [x] **D-092** Choose which changes to apply, item by item, instead of all or nothing.
- [x] **D-093** ★ Never write anything without a preview first.
- [x] **D-094** Hold an item back from a platform deliberately — "Vinted only".
- [x] **D-095** Re-box helper: change a storage code everywhere in one action.

## 9. When a platform needs information Vinted does not have

*(Your example — and it is the workflow that will decide whether this is pleasant
to use.)*

- [x] **D-096** ★★ A queue of items that cannot be listed yet, with only the missing fields shown.
- [x] **D-097** ★ One item per screen, one question at a time, nothing else on show.
      *You said: if possible keep more items loaded in memory, so moving to the next one is quick.*
- [x] **D-098** ★ Remember what you answered for similar items and offer it next time.
- [x] **D-099** Fill from a template by garment type — every midi dress starts the same.
- [x] **D-100** ★ Guess sensible answers from the title and description, for you to confirm.
- [x] **D-101** Bulk-answer one field for many items at once — "all of these are polyester".
- [x] **D-102** Show how many items are waiting, and how long it would take to clear them.
- [x] **D-103** ★ Never block: list to the platforms that are happy, queue the one that is not.
- [x] **D-104** Keyboard-only entry, so a batch can be done without touching the mouse.
- [x] **D-105** Do it from a phone, standing next to the boxes.

## 10. Orders, postage and delivery

- [x] **D-106** ★ An order record the moment something sells, on any platform.
- [x] **D-107** ★ A "Posted" button, with the parcel photo attached.
- [x] **D-108** ★ Store the tracking number.
- [x] **D-109** ★ Check tracking automatically until it is delivered.
- [x] **D-110** ★★ Tell you when a delivery is taking too long.
- [x] **D-111** Tell you when an order has been sitting unposted too long.
- [x] **D-112** A packing list for today's posts.
- [x] **D-113** Print or store the postage label with the order.
- [x] **D-114** Record the actual postage cost, not the estimate.
- [x] **D-115** Handle returns and refunds as their own status.
- [x] **D-116** Flag disputes and cases separately, so they cannot be forgotten.
- [x] **D-117** ★ Everything moves to the archive once completed.
- [x] **D-118** ★ Keep the archive 5 years.
- [x] **D-119** Handle a buyer buying several items at once as one parcel.
- [x] **D-120** Record which box an item came out of, so the empty space is known.

## 11. Buyer messages

- [x] **D-121** ★ Copy the whole conversation into the sale record.
- [x] **D-122** Keep messages arriving after the sale, too.
- [x] **D-123** ★ Tell you when a buyer has sent a message you have not answered.
- [x] **D-124** Saved replies for the questions that come up constantly.
- [x] **D-125** Search every message ever sent.
- [x] **D-126** Flag messages that sound like a complaint.
- [x] **D-127** Keep messages from all three platforms in one place.

## 12. Being told things

- [x] **D-128** ★ Something sold.
- [x] **D-129** ★ Something delivered.
- [x] **D-130** ★★ A delivery is overdue.
- [x] **D-131** ★★ Something is broken — a read failed, a token expired, a platform changed.
- [x] **D-132** ★ Something sold twice.
- [x] **D-133** An offer or a question came in.
- [x] **D-134** A daily summary — sold, posted, delivered, waiting.
- [x] **D-135** A weekly summary with the money in it.
- [x] **D-136** ★ Choose the channel: phone push (ntfy), Telegram, Discord, email.
- [x] **D-137** ★ Quiet hours — nothing at night.
- [x] **D-138** Different urgency for different events.
- [ ] **D-139** Nothing sold in X days on an item — worth a price drop?
- [x] **D-140** ★ Notifications never appear as pop-ups over the screen.

## 13. Money

- [x] **D-141** ★ Record what each item cost.
- [x] **D-142** ★ Job lots — one price for a bag of thirty, split across the items.
- [x] **D-143** Choose how the split works: evenly, or weighted by value.
- [x] **D-144** ★ Profit per item, after fees and postage.
- [x] **D-145** ★ Record platform fees where the platform tells us.
- [x] **D-146** Never guess a fee — leave it blank instead.
- [x] **D-147** ★ Value of everything still unsold.
- [x] **D-148** ★ Totals by month, quarter and year.
- [x] **D-149** Mileage and expenses — car boots, postage supplies.
- [x] **D-150** An export shaped for a self-assessment tax return.
- [x] **D-151** Which platform actually makes the most, after fees.
- [x] **D-152** Average time from buying to selling.
- [x] **D-153** Items that cost more than they sold for.

## 14. Understanding what sells

- [x] **D-154** Best-selling brands.
- [x] **D-155** Best-selling sizes and categories.
- [x] **D-156** How long items take to sell, by type.
- [x] **D-157** Dead stock — listed a year, never sold.
- [x] **D-158** Which photos correlate with a faster sale.
- [x] **D-159** Best day and time to list.
- [x] **D-160** Seasonality — when coats sell.
- [x] **D-161** Price-drop suggestions for items going nowhere.
- [x] **D-162** What is left in each physical box.
- [x] **D-163** Charts. (Say no if charts are noise.)

## 15. Doing it without you

- [x] **D-164** ★ Read Vinted automatically on a schedule.
- [x] **D-165** ★ Choose: fully automatic, or automatic-with-approval.
- [x] **D-166** ★ Automatic for safe things (delisting a sold item), approval for risky things (creating a listing).
- [x] **D-167** A daily list of what it wants to do, that you approve in one press.
- [x] **D-168** Bulk price drops on a schedule.
- [x] **D-169** Relist items that have gone stale, so they resurface.
- [x] **D-170** Pause everything with one switch.
- [x] **D-171** ★ Everything it does is written down and reversible.
- [x] **D-172** Retry automatically when a platform is temporarily unavailable.

## 16. The interface

- [ ] **D-173** ★★ One screen, one job. No dashboard of everything at once.
- [ ] **D-174** ★★ Plain sentences, not tables of data.
- [x] **D-175** ★★ Nothing moves, blinks, slides or pops up.
- [x] **D-176** ★ Detail hidden until asked for.
- [x] **D-177** ★ The same button in the same place, always.
- [x] **D-178** ★ Nothing happens on hover or on selection — only on a press.
- [x] **D-179** ★ Muted colours, no harsh white, no pure black.
- [x] **D-180** ★ Colour never the only way something is shown — always a word too.
- [x] **D-181** Bigger text option.
- [x] **D-182** Dark mode following the system setting.
- [x] **D-183** ★ No jargon anywhere on the first screen.
- [x] **D-184** Works on a phone.
- [x] **D-185** ★ A "what needs me today?" screen and nothing else on it.

## 17. Finding and changing things in bulk

- [x] **D-186** ★ Search everything — title, description, brand, storage code, buyer.
- [x] **D-187** ★ Filter by platform, status, size, brand, box, age.
- [x] **D-188** Saved filters you use often.
- [x] **D-189** ★ Change one field on many items at once.
- [x] **D-190** Find and replace across descriptions.
- [x] **D-191** ★ Find items missing a storage code, or with a duplicate one.
- [x] **D-192** Find items missing photos, sizes or categories.
- [x] **D-193** Find items on one platform but not another.
- [x] **D-194** Print a picking list for a box.

## 18. Not losing anything

- [x] **D-195** ★★ Preview before anything is written. Always.
- [x] **D-196** ★ Never partly-read a catalogue and act as if it were complete.
- [x] **D-197** ★ Every action logged with what it was before and after.
- [x] **D-198** ★ Undo.
- [x] **D-199** A limit on how many changes one run may make without asking.
- [x] **D-200** ★ Test mode that touches nothing real.
- [x] **D-201** Warn before anything irreversible.
- [x] **D-202** ★ Keep the last N runs, not just the last one.
- [x] **D-203** A health check that says plainly whether everything is working.

## 19. The server

- [x] **D-204** ★ One Docker container, one compose file.
- [x] **D-205** ★ Python, matching how you already run things.
- [x] **D-206** ★ Survives a restart, comes back on its own.
- [x] **D-207** ★ Logs you can actually read.
- [x] **D-208** Runs entirely on the home network, nothing exposed.
- [x] **D-209** Reachable from outside, with a password.
      *You said: I use Tailscale across all my devices.*
- [x] **D-210** Uses hardly any memory when idle.
- [x] **D-211** Update by pulling a new image.
- [x] **D-212** ★ Settings in one file you can read and edit.

## 20. Keeping it private

- [x] **D-213** ★ Tokens and keys never in the repo, never in a CSV, never in a log.
- [x] **D-214** ★ Secrets in one place, easy to change when one expires.
- [x] **D-215** ★ Warn before a token expires rather than after.
- [x] **D-216** Buyer addresses stored only as long as needed.
- [x] **D-217** Buyer names removed from the archive after a set time, keeping the money data.
- [x] **D-218** Encrypt the backups.
- [x] **D-219** ★ No third party, no account, no subscription. Ever.

## 21. Moving in from Crosslist

- [x] **D-220** ★★ Import the CSV export from Crosslist — your own data, and by far the fastest way to start.
- [x] **D-221** ★ Compare that import against what Vinted actually shows, to find gaps.
- [x] **D-222** ★ A note of which fields Crosslist keeps, so nothing is lost when you stop paying.
- [x] **D-223** Import the photos it holds too.
- [x] **D-224** Run both side by side for a while before cancelling.
- [x] **D-225** A checklist for the day you cancel the subscription.

## 22. Other places, later

- [ ] **D-226** Depop.
- [ ] **D-227** Etsy.
- [ ] **D-228** Facebook Marketplace.
- [ ] **D-229** Amazon.
- [ ] **D-230** Whatnot / live selling.
- [ ] **D-231** A second Vinted account.
- [x] **D-232** ★ Built so a new platform is one new file, not a rewrite.

## 23. Clever, optional, possibly unnecessary

- [x] **D-233** Write the description automatically from the photos and the fields.
      *You said: have it create the text automatically, but easy for the user to edit or simply replace.*
- [x] **D-234** Suggest a price from what similar items sold for.
- [x] **D-235** Read the care label from a photo.
- [x] **D-236** Recognise the brand from a photo of the label.
- [x] **D-237** Suggest the category from the photo.
- [x] **D-238** Spot a flaw in a photo and flag it.
- [x] **D-239** Barcode or QR label on each physical box.
      *You said: important in future — not needed right now, but I want it ready for when it is used.*
- [ ] **D-240** Print storage-code labels.
- [x] **D-241** Voice notes while photographing, turned into item details.
- [x] **D-242** Rewrite descriptions per platform, in each one's style.
- [x] **D-243** Translate listings for other Vinted countries.
- [ ] **D-244** Suggest which items to bundle together.

## 24. The physical side

- [x] **D-245** ★ Know what is in each box without opening it.
- [x] **D-246** Warn when a box is full.
- [x] **D-247** Suggest where to put a new item.
- [ ] **D-248** ★ Free up a storage code when an item is posted.
- [x] **D-249** A photographing workflow — shoot a batch, assign afterwards.
- [x] **D-250** Bulk-add items from a folder of photos.
- [x] **D-251** Track packaging supplies.
- [x] **D-252** ★ A "what needs posting today" list.

---

## Things I need you to decide, not just tick — answered

**1. Is the Vinted account a business/Pro account?**
> *Currently it's a normal account. It will change eventually but not for at
> least 8 months.*

So: build the browser-session route now, and keep the Vinted connector shaped so
the official Pro API can replace it later without touching anything else.

**2. eBay: API or browser?**
> *Where possible I'd rather use the API on a container. I assume this can all be
> stored in one container but I will do what is best for security and stability.*

Settled: eBay via the Sell API, from the container, with the client secret in the
container's secrets file. One container is fine — see `docs/SYSTEM_ARCHITECTURE.md`.

**3. Automatic or approved?**
> *When manually instigated it should show the plan. But if an item has sold it
> should auto-delist and keep it in a holding place until it has been confirmed
> that it has been sold, so it can be reversed if there is a mistake.*

That is a new feature in its own right — a **reversible holding area** for
automatic delists. Added as X-06.

**4. Who does the data entry, and where?**
> *Both. Entering new items happens next to the boxes. Label printing and packing
> happens at a desk — still using a phone, but there is a laptop or Windows
> tablet if needed.*

So the item-entry screens are phone-first, and the packing screens are
desk-first. Two different shapes, not one compromise.

**5. What do you want to see when you open it?**
> *A dashboard with a menu system on the left, and the main section holds and
> displays what is selected on the menu. The default first page shows: items
> currently on sale, items to be reviewed, items sold, items posted, items in
> archive, and money made this year, month, week and day. Left side menu: To
> table, To post, To review, view list of items, Vinted (a way to load websites
> within the web interface), eBay, sixgenerations.co.uk Shopify website,
> Settings, Console (a way to see what the console is displaying without loading
> it).*

Written up as `docs/INTERFACE_LAYOUT.md`, including the two problems it runs
into: it contradicts the one-screen-one-job rule that was written for the daily
user, and Vinted, eBay and Shopify all actively refuse to be loaded inside
another page.

---

## Still open

- Everything marked `[?]` above — sections 11 to 24, plus D-084 and D-106.
- **"To table"** in the left menu — what does that step mean? Items waiting to be
  photographed, or something else?
- **The existing orders file** you said "needs remaking" — send it and the new
  one can be built to replace it properly rather than guessed at.

The reasoning behind all remaining decisions is in `docs/OPEN_QUESTIONS.md`.
