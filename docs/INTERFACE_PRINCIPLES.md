# Interface Principles — the rules the screens must follow

The person who uses this every day has **autism, ADHD and sensory
sensitivities**. A busy screen is not a matter of taste here — it is the
difference between a tool that gets used and one that gets avoided.

**These rules override normal UI convention. When a rule here conflicts with
"how apps usually look", this file wins.**

---

## 1. The five rules

> ## U-01 and U-02 are retired
>
> Both were put to Kurzon as D-173 (*one screen, one job, no dashboard*) and
> D-174 (*plain sentences, not tables*) on 2026-09-09, and **both were declined**
> — the only two rules in that section he turned down. A **dashboard with tables**
> is what is wanted, and it is specified in `docs/INTERFACE_LAYOUT.md`.
>
> **Every other rule in this file was accepted and still stands.** The design is
> not a compromise: *a dashboard, with tables, that is completely still.*
>
> U-01 and U-02 are kept below for the reasoning, struck through.

### ~~U-01 — One screen, one job~~ *(retired)*
The popup shows the current state and one action. Nothing else. No dashboard, no
tiles, no counters running in the corner. Anything that is not needed right now
lives on another screen that has to be opened deliberately.

### ~~U-02 — Plain language, not data~~ *(retired — but the wording rules in §3 stand)*
> **3 items sold on Vinted. Remove them from eBay?**   [ Show me ]   [ Do it ]

not a table of `sku | vinted_status | ebay_status | shopify_qty`. The table can
exist behind *Show me*. The first thing on screen is a sentence.

### U-03 — Nothing moves on its own
- No animation, no pulsing, no sliding panels, no progress bars that jitter.
- No toasts, no notifications that appear and vanish. Messages stay where they
  are put until they are dismissed.
- No auto-refresh. The screen changes when it is told to.
- `prefers-reduced-motion` is honoured, but the default is already still.

### U-04 — Predictable, always
- The same button is always in the same place, with the same words.
- Nothing happens on hover. Nothing happens on selection. Actions happen on a
  press, and only then.
- No modal dialogs that steal focus. No confirmation chains.
- A run can always be stopped, and stopping is always in the same place.

### U-05 — Detail folded away
Everything technical still exists — logs, diffs, error messages, API responses.
None of it is on the first screen. `Show details` opens it, and the choice is
remembered.

## 2. The visual rules

| Thing | Rule |
|---|---|
| **Colour** | Low saturation. No pure white background, no pure black text — off-white and dark grey. Never red-on-green as the only distinction |
| **Colour meaning** | Colour never carries meaning alone. Every state has a word next to it. "Sold" says *sold* |
| **Contrast** | Meets WCAG AA (4.5:1 body text), but not maximum contrast — harsh contrast is its own sensory problem |
| **Type** | One family, two sizes, two weights. Left-aligned. Never justified, never centred body text |
| **Density** | Generous space. It is better to scroll than to cram |
| **Icons** | Only alongside a word, never instead of one |
| **Sound** | None. Ever |
| **Badges / counts** | Only where a number is genuinely needed. No "12 new!" style attention-grabbing |
| **Dark mode** | Supported, and it follows the system setting. Neither mode is brighter than it needs to be |

## 3. Words

- Short sentences. One idea each.
- No jargon on the first screen: not *sync*, not *parity*, not *SKU*, not *API*.
  Say **check**, **match**, **storage code**, **connection**.
- Numbers written the way they are spoken — "2,041 items", not "2041".
- Errors say what happened and what to do next, in that order. Never a code
  alone.
- Never blame the user. "That didn't connect" not "Invalid credentials supplied".

## 4. What this rules out

Things that would otherwise be normal to build, and must not be:

- A statistics dashboard on the home screen.
- Live progress that updates several times a second — update it at most once a
  second, in words: "Checked 400 of 2,041".
- Notification pop-ups when something sells (F-14 must be opt-in and off by
  default, and must never appear as a screen overlay).
- Multi-step wizards with progress dots.
- Anything that appears while reading something else.
- Tabs within tabs, accordions inside accordions.

## 5. How to check it

Before saying an interface change is done:

1. Open the popup and count everything on screen. If it is more than one
   sentence, one action and one link, justify each extra thing.
2. Watch the screen do nothing for ten seconds. If anything moved, fix it.
3. Read every visible word aloud. Any jargon gets replaced.
4. Turn colour off (greyscale the screen). Every state must still be readable.
5. Set the OS to dark mode and reduced motion, and repeat 1–4.

## 6. Where this came from

General cognitive-accessibility guidance, not a diagnosis-specific standard —
WCAG covers motor, visual and auditory needs well and cognitive needs only
loosely, so most of the above is drawn from neurodivergent UX writing rather than
from a checkable standard.

- [Designing for Neurodivergence — 16 UX principles](https://medium.com/design-bootcamp/beyond-compliance-16-ux-principles-to-truly-include-neurodivergent-users-e7d3ff779665)
- [Principles of Neurodivergent UX Design](https://www.accessibilitychecker.org/blog/neurodivergent-ux-design/)
- [Neurodiversity and UX — Stéphanie Walter](https://stephaniewalter.design/blog/neurodiversity-and-ux-essential-resources-for-cognitive-accessibility/)
- [Designing for neurodivergent and cognitive accessibility — TestParty](https://testparty.ai/blog/neurodivergent-and-cognitive-accessibility-ux)
- [How WCAG benefits everyone: neurodiversity](https://www.wcag.com/blog/digital-accessibility-and-neurodiversity/)

**None of this is a substitute for asking her.** The rules above are a starting
point written from general guidance; the ones that matter are the ones she says
matter. → **Q20**
