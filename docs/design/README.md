# The design and development documents

Four documents that answer *where are we, what is left, and what do I have to do*.

**Open `01_pages.html` in any browser.** Every page links to the other three.

| File | What it is |
|---|---|
| `01_pages.html` | **Every page, drawn.** 23 line diagrams: coloured boxes for each region, a line from each note to the part it describes. Includes pages that do not exist yet |
| `02_pagesInDetail.html` | **What happens on each page.** Every one of the 216 built features allocated to a screen, so nothing is left floating |
| `03_featureStatus.html` | **Every feature and its status**, colour-coded. 312 features since the project began |
| `04_buildSchedule.html` | **The build schedule.** Stages A–K, each sized to be built, tested and merged on its own |

## Why HTML and not Markdown

Markdown cannot draw a box with an arrow pointing at it. These open in any
browser, **print to PDF** from the browser (Ctrl+P), and open in LibreOffice.
No software to install and nothing to pay for.

## They are generated, not typed

```bash
python docs/design/buildDesignDocs.py
```

`03_featureStatus.html` is built from `FEATURE_six-generations_creep.md`, so it
**cannot drift away from the code**. Run the command after any change to the
feature file and the status document is right again.

| File | What it holds |
|---|---|
| `buildDesignDocs.py` | The builder, the build schedule, and which feature belongs to which page |
| `designDocPages.py` | Every page: its regions, its notes, and the questions on it |
| `designDocShared.py` | The look, and the diagram drawer |
| `features.json` | Every feature as data, pulled out of the feature file |

## The orange blocks

An orange block headed **YOU NEED TO FILL THIS IN** is a decision only Kurzon
can make. There are 17 of them, all in `01_pages.html`.

**Every one offers "Claude decides" as a real answer**, so none of them has to
hold the work up. Saying "you choose" to all 17 is a complete answer.
