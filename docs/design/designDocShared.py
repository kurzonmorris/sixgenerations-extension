"""Shared pieces for the four design documents: the look, and the diagram drawer.

The documents are **generated, not written by hand**, so the status document can
never drift away from `FEATURE_six-generations_creep.md`. Run
`python docs/design/buildDesignDocs.py` after any change to the feature file.

HTML rather than Markdown, because Markdown cannot draw a box with an arrow
pointing at it. Every document opens in any browser, prints to PDF from the
browser, and opens in LibreOffice.

The colours follow `docs/INTERFACE_PRINCIPLES.md`: low saturation, no pure white
and no pure black, and **a word beside anything colour is telling you**. Nothing
here relies on colour alone.
"""

from __future__ import annotations

import html

# --- the look ---------------------------------------------------------------

PAPER = "#f4f2ee"
CARD = "#fbfaf7"
INK = "#2a2825"
QUIET = "#6a655e"
LINE = "#ddd8d0"

# Region colours for the page diagrams. Each is paired with a word in the key,
# so the colour is never carrying the meaning on its own.
REGION = {
    "menu":    ("#dfe5e9", "Left menu"),
    "heading": ("#e7e0d3", "Heading"),
    "filter":  ("#dde6dd", "Choosing"),
    "table":   ("#e9e4f0", "A table"),
    "form":    ("#f2e3d8", "Boxes you type in"),
    "action":  ("#e4ded2", "Buttons"),
    "words":   ("#eeeae2", "Words only"),
    "photo":   ("#dde8ea", "Photographs"),
    "missing": ("#f6dede", "NOT BUILT"),
}

STATUS = {
    "built":    ("#3f5f45", "#dfe9e1", "Built and working"),
    "part":     ("#7a5a12", "#f2ead6", "Partly built"),
    "stub":     ("#7a3b3b", "#f6dede", "Refuses on purpose"),
    "planned":  ("#4a4f6a", "#e3e5ef", "Planned, not built"),
    "question": ("#6a4a6a", "#ece0ec", "Needs your answer"),
    "declined": ("#6a655e", "#e8e5df", "Declined"),
}

CSS = f"""
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: {PAPER}; color: {INK};
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  line-height: 1.55; font-size: 16px;
}}
.sheet {{ max-width: 1180px; margin: 0 auto; padding: 2rem 1.5rem 5rem; }}
h1 {{ font-size: 1.9rem; margin: 0 0 .3rem; }}
h2 {{ font-size: 1.3rem; margin: 2.6rem 0 .6rem; padding-top: .8rem;
      border-top: 2px solid {LINE}; }}
h3 {{ font-size: 1.05rem; margin: 1.6rem 0 .4rem; }}
p {{ max-width: 46rem; margin: 0 0 .8rem; }}
.lead {{ color: {QUIET}; max-width: 46rem; }}
a {{ color: #35506b; }}
code {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 3px;
        padding: .05rem .3rem; font-size: .9em; }}
table {{ border-collapse: collapse; width: 100%; margin: .6rem 0 1.4rem;
         font-size: .92rem; background: {CARD}; }}
th, td {{ text-align: left; padding: .45rem .7rem; border: 1px solid {LINE};
          vertical-align: top; }}
th {{ background: #efece6; font-size: .8rem; letter-spacing: .04em;
      text-transform: uppercase; color: {QUIET}; }}
.tag {{ display: inline-block; padding: .08rem .5rem; border-radius: 10px;
        font-size: .78rem; font-weight: 600; white-space: nowrap;
        border: 1px solid rgba(0,0,0,.12); }}
.ask {{ background: #f6ead8; border: 2px solid #b08642; border-radius: 6px;
        padding: .9rem 1.1rem; margin: 1rem 0; max-width: 46rem; }}
.ask b {{ display: block; margin-bottom: .3rem; }}
.ask ul {{ margin: .4rem 0 0 1.1rem; padding: 0; }}
.note {{ background: {CARD}; border-left: 4px solid {LINE};
         padding: .7rem 1rem; margin: 1rem 0; max-width: 46rem; }}
.key {{ display: flex; flex-wrap: wrap; gap: .5rem 1.1rem; margin: .8rem 0 1.6rem;
        font-size: .85rem; }}
.key span {{ display: flex; align-items: center; gap: .4rem; }}
.swatch {{ width: 1rem; height: 1rem; border: 1px solid rgba(0,0,0,.2);
           border-radius: 2px; display: inline-block; }}
figure {{ margin: 1rem 0 2rem; }}
figcaption {{ color: {QUIET}; font-size: .88rem; margin-top: .3rem; }}
svg {{ max-width: 100%; height: auto; background: {CARD};
       border: 1px solid {LINE}; border-radius: 4px; }}
.docnav {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 4px;
           padding: .7rem 1rem; margin: 0 0 2rem; font-size: .92rem; }}
.docnav a {{ margin-right: 1rem; }}
.stamp {{ color: {QUIET}; font-size: .85rem; margin-bottom: 1.6rem; }}
@media print {{ body {{ background: #fff; }} h2 {{ page-break-after: avoid; }}
                figure {{ page-break-inside: avoid; }} }}
"""

NAV = """
<nav class="docnav">
  <b>The four parts:</b>
  <a href="01_pages.html">1. Every page, drawn</a>
  <a href="02_pagesInDetail.html">2. What happens on each page</a>
  <a href="03_featureStatus.html">3. Every feature and its status</a>
  <a href="04_buildSchedule.html">4. The build schedule</a>
</nav>
"""


def esc(text) -> str:
    return html.escape(str(text), quote=False)


def page(title: str, intro: str, body: str, stamp: str) -> str:
    return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><style>{CSS}</style></head>
<body><div class="sheet">
<h1>{esc(title)}</h1>
<p class="stamp">{esc(stamp)}</p>
{NAV}
<p class="lead">{intro}</p>
{body}
</div></body></html>
"""


def ask(question: str, options: list[str]) -> str:
    """A thing only Kurzon can answer. Always offers "Claude decides" as a real option."""
    items = "".join(f"<li>{o}</li>" for o in options)
    return (f'<div class="ask"><b>⬛ YOU NEED TO FILL THIS IN — {esc(question)}</b>'
            f"<ul>{items}</ul></div>")


# --- the diagram drawer ------------------------------------------------------
#
# A page is drawn as a browser frame in the middle, with callout boxes down each
# side and a line from each callout to the region it describes. Boxes, lines and
# colour only — no pictures, as asked for.

FRAME_X, FRAME_W = 340, 470
SIDE_W = 300


def _wrap(text: str, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if len(trial) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def diagram(name: str, regions: list[dict], callouts: list[dict], height: int = 520) -> str:
    """regions: {key, label, y, h, x?, w?}   callouts: {at, side, title, text}"""
    out = [f'<svg viewBox="0 0 1160 {height}" role="img" '
           f'aria-label="Layout of the {esc(name)} page">']
    out.append(f'<rect x="{FRAME_X}" y="18" width="{FRAME_W}" height="{height - 36}" '
               f'rx="6" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    out.append(f'<rect x="{FRAME_X}" y="18" width="{FRAME_W}" height="22" rx="6" '
               f'fill="#ece8e1" stroke="{INK}" stroke-width="2"/>')
    out.append(f'<text x="{FRAME_X + 10}" y="34" font-size="11" fill="{QUIET}">'
               f'{esc(name)}</text>')

    placed = {}
    for region in regions:
        colour, _ = REGION[region["key"]]
        x = region.get("x", FRAME_X + 12)
        w = region.get("w", FRAME_W - 24)
        y, h = region["y"], region["h"]
        placed[region["label"]] = (x, y, w, h)
        dash = ' stroke-dasharray="5 4"' if region["key"] == "missing" else ""
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" '
                   f'fill="{colour}" stroke="{INK}" stroke-width="1"{dash}/>')
        # Wrap to the box's own width, and never draw more lines than fit inside
        # its height. A label that spills outside its box is worse than a short one.
        fits = max(1, int((h - 8) / 13))
        pieces = _wrap(region["label"], max(8, int((w - 14) / 5.9)))
        if len(pieces) > fits:
            pieces = pieces[:fits]
            pieces[-1] = pieces[-1][:max(4, int((w - 14) / 5.9) - 1)] + "…"
        for n, piece in enumerate(pieces):
            out.append(f'<text x="{x + 7}" y="{y + 15 + n * 13}" font-size="10" '
                       f'fill="{INK}">{esc(piece)}</text>')

    for call in callouts:
        target = placed.get(call["at"])
        if not target:
            continue
        tx, ty, tw, th = target
        left = call.get("side", "left") == "left"
        bx = 14 if left else FRAME_X + FRAME_W + 46
        by = call["y"]
        lines = _wrap(call["text"], 44)
        bh = 20 + len(lines) * 13
        out.append(f'<rect x="{bx}" y="{by}" width="{SIDE_W}" height="{bh}" rx="4" '
                   f'fill="{CARD}" stroke="{QUIET}" stroke-width="1"/>')
        out.append(f'<text x="{bx + 9}" y="{by + 15}" font-size="11" font-weight="700" '
                   f'fill="{INK}">{esc(call["title"])}</text>')
        for n, piece in enumerate(lines):
            out.append(f'<text x="{bx + 9}" y="{by + 30 + n * 13}" font-size="10.5" '
                       f'fill="{QUIET}">{esc(piece)}</text>')
        sx = bx + SIDE_W if left else bx
        sy = by + bh / 2
        ex = tx if left else tx + tw
        ey = ty + th / 2
        mid = (sx + ex) / 2
        out.append(f'<path d="M {sx} {sy} C {mid} {sy}, {mid} {ey}, {ex} {ey}" '
                   f'fill="none" stroke="{QUIET}" stroke-width="1.4"/>')
        out.append(f'<circle cx="{ex}" cy="{ey}" r="3.2" fill="{QUIET}"/>')

    out.append("</svg>")
    return "".join(out)


def regionKey() -> str:
    parts = "".join(
        f'<span><i class="swatch" style="background:{c}"></i>{esc(w)}</span>'
        for c, w in REGION.values())
    return f'<div class="key">{parts}</div>'


def statusKey() -> str:
    parts = "".join(
        f'<span><i class="swatch" style="background:{bg};border-color:{fg}"></i>{esc(w)}</span>'
        for fg, bg, w in STATUS.values())
    return f'<div class="key">{parts}</div>'


def tag(kind: str) -> str:
    fg, bg, word = STATUS[kind]
    return f'<span class="tag" style="color:{fg};background:{bg}">{esc(word)}</span>'
