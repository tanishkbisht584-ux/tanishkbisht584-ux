"""Neofetch-style info card. Rows fade in on a stagger so the panel 'prints'.

Layout is a fixed two-column grid rather than right-aligned values: with
multi-line entries (Learning, Projects) a right edge has nothing to align to.
Card width is measured from the longest value, so editing config.json never
overflows the panel.
"""
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
PAL = CFG["palette"]

PAD = 22
ROW = 24
GAP = 12          # blank space between groups
FS = 13
LABEL_W = 132
CHAR_W = FS * 0.60   # monospace advance at this size
STATIC = os.environ.get("STATIC") == "1"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def flatten():
    """[(label|None, line, is_first_line)] with None marking a group spacer."""
    out = []
    for gi, group in enumerate(CFG["card"]):
        if gi:
            out.append((None, None, False))
        for label, value in group:
            lines = value if isinstance(value, list) else [value]
            for li, line in enumerate(lines):
                out.append((label if li == 0 else "", line, li == 0))
    return out


def build():
    body = flatten()
    longest = max((len(v) for _, v, _ in body if v), default=20)
    w = int(PAD * 2 + LABEL_W + longest * CHAR_W) + 16
    rows = sum(ROW if lbl is not None else GAP for lbl, _, _ in body)
    h = PAD * 2 + 34 + rows + 6

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">',
        f'<rect width="{w}" height="{h}" rx="10" fill="{PAL["bg"]}" '
        f'stroke="{PAL["chrome"]}" stroke-opacity=".35"/>',
    ]
    if not STATIC:
        p += ["<style>",
              "@keyframes in{from{opacity:0;transform:translateX(-10px)}"
              "to{opacity:1;transform:none}}",
              ".r{opacity:0;animation:in .4s ease-out forwards}",
              "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1}}",
              "</style>"]

    p.append(f'<text x="{PAD}" y="{PAD + 14}" font-size="{FS}" fill="{PAL["chrome"]}">'
             f'{esc(CFG["username"])}@github</text>')
    p.append(f'<line x1="{PAD}" y1="{PAD + 24}" x2="{w - PAD}" y2="{PAD + 24}" '
             f'stroke="{PAL["chrome"]}" stroke-opacity=".3"/>')

    y = PAD + 34 + FS
    i = 0
    for label, line, first in body:
        if label is None:
            y += GAP
            continue
        cls = "" if STATIC else f' class="r" style="animation-delay:{0.05 * i + 0.15:.2f}s"'
        p.append(f"<g{cls}>")
        if label:
            p.append(f'<text x="{PAD}" y="{y}" font-size="{FS}" '
                     f'fill="{PAL["accent"]}">{esc(label)}</text>')
        p.append(f'<text x="{PAD + LABEL_W}" y="{y}" font-size="{FS}" '
                 f'fill="{PAL["muted"] if not first else PAL["text"]}">{esc(line)}</text>')
        p.append("</g>")
        y += ROW
        i += 1

    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    out = ROOT / "info-card.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")
