# Do you want these features?

Everything I can think of that this system could do. **Put an `x` in the
brackets** for anything you want — `- [x]` — and leave the rest alone. A blank
box is not a "no", it is "not yet"; cross one out with `~~` if it is a definite
no and I will record it as declined so it does not come round again.

**★ = I would recommend it**, usually because it prevents a loss or saves
repeated manual work.

Nothing here is built. Nothing here commits you to anything. Marked items move
into `FEATURE_six-generations_creep.md` Part D and get built in order.

**If a section is irrelevant, write "skip section" at the top of it** rather than
reading 20 lines.

---

## 1. Getting the data out of Vinted

- [ ] **D-001** ★ One button that reads the entire wardrobe, every item, every field.
- [ ] **D-002** ★ Only fetch what changed since last time, instead of everything.
- [ ] **D-003** Read sold items as well as live ones.
- [ ] **D-004** ★ Read the full item detail page, not just the summary — more fields live there.
- [ ] **D-005** Read draft/unpublished items.
- [ ] **D-006** Read hidden/reserved items.
- [ ] **D-007** ★ Record the date each item was uploaded.
- [ ] **D-008** Record how many views and likes each item has.
- [ ] **D-009** Record how long an item has been listed.
- [ ] **D-010** ★ Warn when Vinted changes something and the read stops working properly.
- [ ] **D-011** Read the whole Vinted category tree once, so categories can be matched later.
- [ ] **D-012** Read your Vinted bundles/discounts.
- [ ] **D-013** Read offers received on items.
- [ ] **D-014** ★ Check whether the account qualifies for Vinted's official business API (would replace most of the above with something supported).

## 2. The detail stored against each item

- [ ] **D-015** ★ Multiple sizes per item — UK, EU, US, Italian, letter, all at once.
- [ ] **D-016** ★ Actual garment measurements — chest, waist, length, sleeve, shoulder, hem.
- [ ] **D-017** Measurements in both cm and inches, converted automatically.
- [ ] **D-018** ★ Multiple colours per item, with one marked as the main one.
- [ ] **D-019** ★ Multiple categories per item, and a different one per platform.
- [ ] **D-020** Material composition as a list — 70% wool, 30% polyester.
- [ ] **D-021** ★ Condition in your own words, kept separate from each platform's fixed list.
- [ ] **D-022** ★ Flaws recorded individually, each with its own photo.
- [ ] **D-023** Style, fit, pattern, neckline, sleeve length, occasion — the fields eBay asks for.
- [ ] **D-024** Era / decade, for vintage.
- [ ] **D-025** Made-in country.
- [ ] **D-026** Care instructions from the label.
- [ ] **D-027** ★ Weight and parcel size, for postage.
- [ ] **D-028** Original retail price, if known.
- [ ] **D-029** ★ A permanent internal id per garment, so re-boxing cannot break anything.
- [ ] **D-030** Free-text private notes never shown to a buyer.

## 3. Photos

- [ ] **D-031** ★ Download and keep every photo at full resolution.
- [ ] **D-032** ★ Keep them numbered in the exact order they were originally set.
- [ ] **D-033** ★ Never download or upload the same image twice (matched by content).
- [ ] **D-034** Label photos by what they are — main, label, flaw, measurement, parcel.
- [ ] **D-035** Automatically resize per platform, keeping the original untouched.
- [ ] **D-036** Reorder photos by dragging, and push the new order everywhere.
- [ ] **D-037** Add photos that were never on Vinted.
- [ ] **D-038** ★ Photo of the parcel in its bag, attached to the order.
- [ ] **D-039** Watermark photos going to some platforms.
- [ ] **D-040** Remove or whiten the background automatically.
- [ ] **D-041** Straighten and crop automatically.
- [ ] **D-042** Warn when an item has fewer photos than a platform wants.

## 4. Where the data lives

- [ ] **D-043** ★ A proper database rather than files as the store (CSVs still exported).
- [ ] **D-044** ★ Start on SQLite — one file, no admin, copies like any other file.
- [ ] **D-045** Postgres instead, from day one.
- [ ] **D-046** ★ Everything on the server in Docker, not in the browser.
- [ ] **D-047** ★ Survives the move from Unraid to HexOS with no changes.
- [ ] **D-048** ★ Nightly automatic backup of database and photos.
- [ ] **D-049** Keep a version history of every item, so you can see what changed and when.
- [ ] **D-050** ★ Nothing is ever deleted — items change status instead.
- [ ] **D-051** Restore-from-backup that you can actually test.
- [ ] **D-052** Export everything to a single zip you could hand to an accountant.

## 5. The spreadsheet files

- [ ] **D-053** ★ `onsale_inventory.csv` — everything currently for sale.
- [ ] **D-054** ★ `sold_items.csv` — the item, the sale, the postage, the messages.
- [ ] **D-055** ★ `orders.csv` — a short line per sale.
- [ ] **D-056** ★ `archive.csv` — completed sales, kept 5 years.
- [ ] **D-057** ★ Files rewritten automatically whenever something changes.
- [ ] **D-058** Files also written on a schedule, so there is always a recent copy.
- [ ] **D-059** ★ Edit a CSV by hand and have the system read the changes back in.
- [ ] **D-060** Excel-format (.xlsx) versions as well as CSV.
- [ ] **D-061** A Google Sheet that updates itself, so purchases can be typed on a phone.
- [ ] **D-062** ★ Multi-value fields flattened predictably — `size_uk`, `size_eu`, and a catch-all.
- [ ] **D-063** A separate `purchases.csv` for what things cost.

## 6. Putting items on eBay

- [ ] **D-064** ★ Create an eBay listing from an item already on Vinted.
- [ ] **D-065** ★ Update an eBay price when it changes elsewhere.
- [ ] **D-066** ★ End an eBay listing the moment the item sells elsewhere.
- [ ] **D-067** ★ Put the storage code in eBay's SKU field, where it is an exact match.
- [ ] **D-068** Map Vinted categories to eBay categories automatically.
- [ ] **D-069** Fill eBay item specifics (brand, size, colour, style) from what we hold.
- [ ] **D-070** ★ Reusable postage / returns / payment policies so every listing does not ask again.
- [ ] **D-071** Listing templates per garment type — dresses always described the same way.
- [ ] **D-072** eBay-specific pricing — higher than Vinted, because the fees are.
- [ ] **D-073** Best-offer settings per item.
- [ ] **D-074** Schedule listings to go live at a chosen time.
- [ ] **D-075** ★ Read eBay orders and fees back for the accounts.

## 7. Putting items on the Shopify site

- [ ] **D-076** ★ Create a Shopify product from an item already on Vinted.
- [ ] **D-077** ★ Keep prices in step.
- [ ] **D-078** ★ Set stock to zero the moment it sells elsewhere.
- [ ] **D-079** Put items into Shopify collections automatically, by category or brand.
- [ ] **D-080** Tag products automatically — era, colour, size, condition.
- [ ] **D-081** Sizes and colours as proper variant options rather than text.
- [ ] **D-082** SEO title and description generated from the item.
- [ ] **D-083** ★ Read Shopify orders back for the accounts.
- [ ] **D-084** Publish to Shopify as a draft first, for a look before it goes live.

## 8. Keeping all three in step

- [ ] **D-085** ★★ **Sold anywhere → removed everywhere**, automatically. The single most valuable thing here.
- [ ] **D-086** ★ One screen showing every item and which platforms it is on.
- [ ] **D-087** ★ Warn when the same item sold twice before a check ran.
- [ ] **D-088** ★ Decide per field which platform wins — price, stock, description, photos.
- [ ] **D-089** Different price per platform, by a rule — eBay +15%, say.
- [ ] **D-090** Ask rather than guess when both sides changed since last time.
- [ ] **D-091** ★ Undo the last run.
- [ ] **D-092** Choose which changes to apply, item by item, instead of all or nothing.
- [ ] **D-093** ★ Never write anything without a preview first.
- [ ] **D-094** Hold an item back from a platform deliberately — "Vinted only".
- [ ] **D-095** Re-box helper: change a storage code everywhere in one action.

## 9. When a platform needs information Vinted does not have

*(Your example — and it is the workflow that will decide whether this is pleasant
to use.)*

- [ ] **D-096** ★★ A queue of items that cannot be listed yet, with only the missing fields shown.
- [ ] **D-097** ★ One item per screen, one question at a time, nothing else on show.
- [ ] **D-098** ★ Remember what you answered for similar items and offer it next time.
- [ ] **D-099** Fill from a template by garment type — every midi dress starts the same.
- [ ] **D-100** ★ Guess sensible answers from the title and description, for you to confirm.
- [ ] **D-101** Bulk-answer one field for many items at once — "all of these are polyester".
- [ ] **D-102** Show how many items are waiting, and how long it would take to clear them.
- [ ] **D-103** ★ Never block: list to the platforms that are happy, queue the one that is not.
- [ ] **D-104** Keyboard-only entry, so a batch can be done without touching the mouse.
- [ ] **D-105** Do it from a phone, standing next to the boxes.

## 10. Orders, postage and delivery

- [ ] **D-106** ★ An order record the moment something sells, on any platform.
- [ ] **D-107** ★ A "Posted" button, with the parcel photo attached.
- [ ] **D-108** ★ Store the tracking number.
- [ ] **D-109** ★ Check tracking automatically until it is delivered.
- [ ] **D-110** ★★ Tell you when a delivery is taking too long.
- [ ] **D-111** Tell you when an order has been sitting unposted too long.
- [ ] **D-112** A packing list for today's posts.
- [ ] **D-113** Print or store the postage label with the order.
- [ ] **D-114** Record the actual postage cost, not the estimate.
- [ ] **D-115** Handle returns and refunds as their own status.
- [ ] **D-116** Flag disputes and cases separately, so they cannot be forgotten.
- [ ] **D-117** ★ Everything moves to the archive once completed.
- [ ] **D-118** ★ Keep the archive 5 years.
- [ ] **D-119** Handle a buyer buying several items at once as one parcel.
- [ ] **D-120** Record which box an item came out of, so the empty space is known.

## 11. Buyer messages

- [ ] **D-121** ★ Copy the whole conversation into the sale record.
- [ ] **D-122** Keep messages arriving after the sale, too.
- [ ] **D-123** ★ Tell you when a buyer has sent a message you have not answered.
- [ ] **D-124** Saved replies for the questions that come up constantly.
- [ ] **D-125** Search every message ever sent.
- [ ] **D-126** Flag messages that sound like a complaint.
- [ ] **D-127** Keep messages from all three platforms in one place.

## 12. Being told things

- [ ] **D-128** ★ Something sold.
- [ ] **D-129** ★ Something delivered.
- [ ] **D-130** ★★ A delivery is overdue.
- [ ] **D-131** ★★ Something is broken — a read failed, a token expired, a platform changed.
- [ ] **D-132** ★ Something sold twice.
- [ ] **D-133** An offer or a question came in.
- [ ] **D-134** A daily summary — sold, posted, delivered, waiting.
- [ ] **D-135** A weekly summary with the money in it.
- [ ] **D-136** ★ Choose the channel: phone push (ntfy), Telegram, Discord, email.
- [ ] **D-137** ★ Quiet hours — nothing at night.
- [ ] **D-138** Different urgency for different events.
- [ ] **D-139** Nothing sold in X days on an item — worth a price drop?
- [ ] **D-140** ★ Notifications never appear as pop-ups over the screen.

## 13. Money

- [ ] **D-141** ★ Record what each item cost.
- [ ] **D-142** ★ Job lots — one price for a bag of thirty, split across the items.
- [ ] **D-143** Choose how the split works: evenly, or weighted by value.
- [ ] **D-144** ★ Profit per item, after fees and postage.
- [ ] **D-145** ★ Record platform fees where the platform tells us.
- [ ] **D-146** Never guess a fee — leave it blank instead.
- [ ] **D-147** ★ Value of everything still unsold.
- [ ] **D-148** ★ Totals by month, quarter and year.
- [ ] **D-149** Mileage and expenses — car boots, postage supplies.
- [ ] **D-150** An export shaped for a self-assessment tax return.
- [ ] **D-151** Which platform actually makes the most, after fees.
- [ ] **D-152** Average time from buying to selling.
- [ ] **D-153** Items that cost more than they sold for.

## 14. Understanding what sells

- [ ] **D-154** Best-selling brands.
- [ ] **D-155** Best-selling sizes and categories.
- [ ] **D-156** How long items take to sell, by type.
- [ ] **D-157** Dead stock — listed a year, never sold.
- [ ] **D-158** Which photos correlate with a faster sale.
- [ ] **D-159** Best day and time to list.
- [ ] **D-160** Seasonality — when coats sell.
- [ ] **D-161** Price-drop suggestions for items going nowhere.
- [ ] **D-162** What is left in each physical box.
- [ ] **D-163** Charts. (Say no if charts are noise.)

## 15. Doing it without you

- [ ] **D-164** ★ Read Vinted automatically on a schedule.
- [ ] **D-165** ★ Choose: fully automatic, or automatic-with-approval.
- [ ] **D-166** ★ Automatic for safe things (delisting a sold item), approval for risky things (creating a listing).
- [ ] **D-167** A daily list of what it wants to do, that you approve in one press.
- [ ] **D-168** Bulk price drops on a schedule.
- [ ] **D-169** Relist items that have gone stale, so they resurface.
- [ ] **D-170** Pause everything with one switch.
- [ ] **D-171** ★ Everything it does is written down and reversible.
- [ ] **D-172** Retry automatically when a platform is temporarily unavailable.

## 16. The interface

- [ ] **D-173** ★★ One screen, one job. No dashboard of everything at once.
- [ ] **D-174** ★★ Plain sentences, not tables of data.
- [ ] **D-175** ★★ Nothing moves, blinks, slides or pops up.
- [ ] **D-176** ★ Detail hidden until asked for.
- [ ] **D-177** ★ The same button in the same place, always.
- [ ] **D-178** ★ Nothing happens on hover or on selection — only on a press.
- [ ] **D-179** ★ Muted colours, no harsh white, no pure black.
- [ ] **D-180** ★ Colour never the only way something is shown — always a word too.
- [ ] **D-181** Bigger text option.
- [ ] **D-182** Dark mode following the system setting.
- [ ] **D-183** ★ No jargon anywhere on the first screen.
- [ ] **D-184** Works on a phone.
- [ ] **D-185** ★ A "what needs me today?" screen and nothing else on it.

## 17. Finding and changing things in bulk

- [ ] **D-186** ★ Search everything — title, description, brand, storage code, buyer.
- [ ] **D-187** ★ Filter by platform, status, size, brand, box, age.
- [ ] **D-188** Saved filters you use often.
- [ ] **D-189** ★ Change one field on many items at once.
- [ ] **D-190** Find and replace across descriptions.
- [ ] **D-191** ★ Find items missing a storage code, or with a duplicate one.
- [ ] **D-192** Find items missing photos, sizes or categories.
- [ ] **D-193** Find items on one platform but not another.
- [ ] **D-194** Print a picking list for a box.

## 18. Not losing anything

- [ ] **D-195** ★★ Preview before anything is written. Always.
- [ ] **D-196** ★ Never partly-read a catalogue and act as if it were complete.
- [ ] **D-197** ★ Every action logged with what it was before and after.
- [ ] **D-198** ★ Undo.
- [ ] **D-199** A limit on how many changes one run may make without asking.
- [ ] **D-200** ★ Test mode that touches nothing real.
- [ ] **D-201** Warn before anything irreversible.
- [ ] **D-202** ★ Keep the last N runs, not just the last one.
- [ ] **D-203** A health check that says plainly whether everything is working.

## 19. The server

- [ ] **D-204** ★ One Docker container, one compose file.
- [ ] **D-205** ★ Python, matching how you already run things.
- [ ] **D-206** ★ Survives a restart, comes back on its own.
- [ ] **D-207** ★ Logs you can actually read.
- [ ] **D-208** Runs entirely on the home network, nothing exposed.
- [ ] **D-209** Reachable from outside, with a password.
- [ ] **D-210** Uses hardly any memory when idle.
- [ ] **D-211** Update by pulling a new image.
- [ ] **D-212** ★ Settings in one file you can read and edit.

## 20. Keeping it private

- [ ] **D-213** ★ Tokens and keys never in the repo, never in a CSV, never in a log.
- [ ] **D-214** ★ Secrets in one place, easy to change when one expires.
- [ ] **D-215** ★ Warn before a token expires rather than after.
- [ ] **D-216** Buyer addresses stored only as long as needed.
- [ ] **D-217** Buyer names removed from the archive after a set time, keeping the money data.
- [ ] **D-218** Encrypt the backups.
- [ ] **D-219** ★ No third party, no account, no subscription. Ever.

## 21. Moving in from Crosslist

- [ ] **D-220** ★★ Import the CSV export from Crosslist — your own data, and by far the fastest way to start.
- [ ] **D-221** ★ Compare that import against what Vinted actually shows, to find gaps.
- [ ] **D-222** ★ A note of which fields Crosslist keeps, so nothing is lost when you stop paying.
- [ ] **D-223** Import the photos it holds too.
- [ ] **D-224** Run both side by side for a while before cancelling.
- [ ] **D-225** A checklist for the day you cancel the subscription.

## 22. Other places, later

- [ ] **D-226** Depop.
- [ ] **D-227** Etsy.
- [ ] **D-228** Facebook Marketplace.
- [ ] **D-229** Amazon.
- [ ] **D-230** Whatnot / live selling.
- [ ] **D-231** A second Vinted account.
- [ ] **D-232** ★ Built so a new platform is one new file, not a rewrite.

## 23. Clever, optional, possibly unnecessary

- [ ] **D-233** Write the description automatically from the photos and the fields.
- [ ] **D-234** Suggest a price from what similar items sold for.
- [ ] **D-235** Read the care label from a photo.
- [ ] **D-236** Recognise the brand from a photo of the label.
- [ ] **D-237** Suggest the category from the photo.
- [ ] **D-238** Spot a flaw in a photo and flag it.
- [ ] **D-239** Barcode or QR label on each physical box.
- [ ] **D-240** Print storage-code labels.
- [ ] **D-241** Voice notes while photographing, turned into item details.
- [ ] **D-242** Rewrite descriptions per platform, in each one's style.
- [ ] **D-243** Translate listings for other Vinted countries.
- [ ] **D-244** Suggest which items to bundle together.

## 24. The physical side

- [ ] **D-245** ★ Know what is in each box without opening it.
- [ ] **D-246** Warn when a box is full.
- [ ] **D-247** Suggest where to put a new item.
- [ ] **D-248** ★ Free up a storage code when an item is posted.
- [ ] **D-249** A photographing workflow — shoot a batch, assign afterwards.
- [ ] **D-250** Bulk-add items from a folder of photos.
- [ ] **D-251** Track packaging supplies.
- [ ] **D-252** ★ A "what needs posting today" list.

---

## Things I need you to decide, not just tick

These are not features, they are forks in the road. A one-line answer to each
unblocks a lot:

1. **Is the Vinted account a business/Pro account?** If yes, Vinted has an
   official API and half of this gets easier and safer.
2. **eBay: API or browser?** The API needs a secret kept somewhere; the container
   can keep one, an extension cannot.
3. **Automatic or approved?** Should the system delist and list on its own, or
   show you the plan first?
4. **Who does the data entry, and where?** At a desk, or on a phone next to the
   boxes?
5. **What do you actually want to see when you open it?** One sentence would do.

The full list, with my reasoning, is in `docs/OPEN_QUESTIONS.md`.
