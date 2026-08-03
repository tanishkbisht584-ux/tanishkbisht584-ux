"""Writes both terminal panels:

  info-card.svg    header block (USER/ROLE/...), sits beside the portrait
  skills-card.svg  the sections, balanced across 3 columns, full width below

The sections are ~90 lines. In one column beside a 370px portrait that is a
2000px tower, so they get their own wide panel and are bin-packed into columns
of near-equal height. Dividers are real <line> elements - box-drawing glyphs
fall back to tofu in whatever monospace the browser resolves.
"""
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
PAL = CFG["palette"]
STATIC = os.environ.get("STATIC") == "1"

FS = 12
ROW = 18
PAD = 22
COLS = 3
CARD_W = 880


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def anim(i, delay=0.04, start=0.15):
    if STATIC:
        return ""
    return f' class="r" style="animation-delay:{start + i * delay:.2f}s"'


STYLE = ("<style>"
         "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
         ".r{opacity:0;animation:in .35s ease-out forwards}"
         "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1}}"
         "</style>")


# ---------------------------------------------------------------- header card

def info_card():
    rows = CFG["header"]
    label_w = 96
    longest = max(len(v) for _, v in rows)
    w = int(PAD * 2 + label_w + longest * FS * 0.60) + 12
    h = PAD * 2 + 30 + len(rows) * ROW + 8

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace">',
         f'<rect width="{w}" height="{h}" rx="10" fill="{PAL["bg"]}" '
         f'stroke="{PAL["chrome"]}" stroke-opacity=".35"/>']
    if not STATIC:
        p.append(STYLE)

    p.append(f'<text x="{PAD}" y="{PAD + 12}" font-size="{FS}" '
             f'fill="{PAL["chrome"]}">SYSTEM PROFILE</text>')
    p.append(f'<line x1="{PAD}" y1="{PAD + 22}" x2="{w - PAD}" y2="{PAD + 22}" '
             f'stroke="{PAL["chrome"]}" stroke-opacity=".3"/>')

    y = PAD + 30 + FS
    for i, (k, v) in enumerate(rows):
        p.append(f"<g{anim(i)}>")
        p.append(f'<text x="{PAD}" y="{y}" font-size="{FS}" '
                 f'fill="{PAL["accent"]}">{esc(k)}</text>')
        p.append(f'<text x="{PAD + label_w}" y="{y}" font-size="{FS}" '
                 f'fill="{PAL["text"]}">{esc(v)}</text>')
        p.append("</g>")
        y += ROW
    p.append("</svg>")
    return "\n".join(p)


# ---------------------------------------------------------------- skills card

def _lines(sec):
    """Row cost of a section: title + rule + one row per item line."""
    n = 0
    for it in sec["items"]:
        n += 2 if isinstance(it, list) else 1
    return n + 2


def _pack(sections):
    """Greedy: each section joins the currently shortest column."""
    cols = [[] for _ in range(COLS)]
    load = [0] * COLS
    for sec in sections:
        i = load.index(min(load))
        cols[i].append(sec)
        load[i] += _lines(sec) + 1        # +1 blank row between sections
    return cols, max(load)


def skills_card():
    cols, tallest = _pack(CFG["sections"])
    col_w = (CARD_W - PAD * 2) // COLS
    h = PAD * 2 + tallest * ROW + 10

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{h}" '
         f'viewBox="0 0 {CARD_W} {h}" '
         f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace">',
         f'<rect width="{CARD_W}" height="{h}" rx="10" fill="{PAL["bg"]}" '
         f'stroke="{PAL["chrome"]}" stroke-opacity=".35"/>']
    if not STATIC:
        p.append(STYLE)

    i = 0
    for ci, col in enumerate(cols):
        x = PAD + ci * col_w
        y = PAD + FS
        for sec in col:
            p.append(f'<g{anim(i, 0.02)}><text x="{x}" y="{y}" font-size="{FS}" '
                     f'fill="{PAL["chrome"]}">{esc(sec["title"])}</text></g>')
            y += 6
            p.append(f'<line x1="{x}" y1="{y}" x2="{x + col_w - 18}" y2="{y}" '
                     f'stroke="{PAL["chrome"]}" stroke-opacity=".25"/>')
            y += ROW - 6
            i += 1

            for it in sec["items"]:
                if isinstance(it, list):
                    name, desc = it
                    p.append(f'<g{anim(i, 0.02)}><text x="{x}" y="{y}" font-size="{FS}" '
                             f'fill="{PAL["accent"]}">&gt; {esc(name)}</text></g>')
                    y += ROW
                    p.append(f'<g{anim(i, 0.02)}><text x="{x + 12}" y="{y}" '
                             f'font-size="{FS - 1}" fill="{PAL["muted"]}" '
                             f'fill-opacity=".8">{esc(desc)}</text></g>')
                else:
                    p.append(f'<g{anim(i, 0.02)}><text x="{x}" y="{y}" font-size="{FS}" '
                             f'fill="{PAL["muted"]}">- {esc(it)}</text></g>')
                y += ROW
                i += 1
            y += ROW

    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    for name, body in (("info-card.svg", info_card()),
                       ("skills-card.svg", skills_card())):
        (ROOT / name).write_text(body, encoding="utf-8")
        print(f"wrote {name} ({(ROOT / name).stat().st_size // 1024} KB)")

    cols, tallest = _pack(CFG["sections"])
    print("column balance:", [sum(_lines(s) + 1 for s in c) for c in cols],
          f"-> tallest {tallest} rows")
