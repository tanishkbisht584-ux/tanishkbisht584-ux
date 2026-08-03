"""Photo -> ASCII character portrait as SVG (dark + light variants).

    python make_ascii_svg.py photo.jpg

The dot-dither pipeline (make_portrait_svg.py) is the higher-fidelity option;
this is the terminal-looking one. Glyphs do mush below ~2px, so this is built
at a ~85x58 grid meant to display around 370px wide - not at the dense grid
the dot portrait uses.

Ink direction is per-theme, same rule as the dots: characters must contrast
with the plate, or the portrait reads as a negative.
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
PAL = CFG["palette"]

ROWS = 58
FS = 8                      # px per line
CHAR_W = 0.60 * FS          # monospace advance
SRC_W, SRC_H = 300, 340     # portrait aspect to preserve
COLS = int(round(ROWS * (SRC_W / SRC_H) / 0.60))

CONTRAST = 1.6
TARGET_MEAN = 138           # same exposure knob as the dot portrait
FLOOR = 0.42                # below this density a cell prints a space; raise to
                            # blank more background, lower to keep more detail

# leading space clears the background to nothing; density rises left to right
RAMP = " .`:-=+*csS#%@"


def prep(path):
    im = Image.open(path).convert("RGB")
    target = SRC_W / SRC_H
    w, h = im.size
    if w / h > target:
        nw = int(h * target)
        im = im.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
    else:
        im = im.crop((0, 0, w, int(w / target)))

    g = ImageOps.autocontrast(im.convert("L").resize((COLS, ROWS), Image.LANCZOS), cutoff=1)
    a = np.asarray(g, dtype=np.float32) / 255.0
    gamma = np.log(TARGET_MEAN / 255.0) / np.log(max(a.mean(), 1e-3))
    g = Image.fromarray((np.clip(a ** gamma, 0, 1) * 255).astype(np.uint8))
    g = ImageEnhance.Contrast(g).enhance(CONTRAST)
    return g.filter(ImageFilter.UnsharpMask(2, 120, 3))


def to_rows(gray, lit):
    """Map brightness to glyphs, sparse -> dense along RAMP.

    lit=True  (dark plate): density follows brightness, so the lit face prints
    lit=False (light plate): density follows darkness, so hair and suit print

    Everything below FLOOR collapses to the space glyph. Without it the mid-grey
    backdrop lands mid-ramp and fills the frame with '*' and 'c', leaving the
    face nothing to stand against.
    """
    a = np.asarray(gray, dtype=np.float32) / 255.0
    density = a if lit else 1.0 - a
    density = np.clip((density - FLOOR) / (1.0 - FLOOR), 0.0, 1.0)
    idx = (density * (len(RAMP) - 1)).round().astype(int)
    return ["".join(RAMP[i] for i in row) for row in idx]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(rows, colour, bg):
    w = int(COLS * CHAR_W) + 16
    h = ROWS * FS + 16
    plate = "" if bg is None else f'<rect width="{w}" height="{h}" rx="6" fill="{bg}"/>'
    per = 0.028   # stagger between rows; whole print lands in ~1.9s

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace">',
        plate,
        "<style>",
        # wipe left-to-right; if clip-path is unsupported the row simply shows
        "@keyframes wipe{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}",
        f".l{{clip-path:inset(0 100% 0 0);animation:wipe .32s steps({COLS},end) forwards}}",
        "@media (prefers-reduced-motion:reduce){.l{animation:none;clip-path:none}}",
        "</style>",
    ]
    for i, line in enumerate(rows):
        y = 8 + (i + 1) * FS
        out.append(f'<text class="l" x="8" y="{y}" font-size="{FS}" fill="{colour}" '
                   f'xml:space="preserve" style="animation-delay:{i * per:.2f}s">'
                   f"{esc(line)}</text>")
    out.append("</svg>")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: make_ascii_svg.py <photo>")
    photo = pathlib.Path(sys.argv[1])
    if not photo.exists():
        sys.exit(f"no such file: {photo}")

    gray = prep(photo)
    for fname, colour, bg, inv in (
        ("ascii-light.svg", "#0F172A", None, False),
        ("ascii-dark.svg", PAL["portrait"], PAL["bg"], True),
    ):
        rows = to_rows(gray, inv)
        (ROOT / fname).write_text(build(rows, colour, bg), encoding="utf-8")
        blank = sum(r.count(" ") for r in rows) / (COLS * ROWS)
        print(f"{fname}: {COLS}x{ROWS} chars, {blank:.0%} blank, "
              f"{(ROOT / fname).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
