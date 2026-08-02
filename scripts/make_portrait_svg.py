"""Photo -> 1-bit dithered dot portrait as SVG (dark + light variants).

    python make_portrait_svg.py photo.jpg

Dots are emitted as run-length <path> segments with shape-rendering=crispEdges.
Font glyphs mush below ~2px - that is why this is not ASCII art.

No background segmentation. The reference pipeline removes the backdrop for
dark mode, which assumes the subject separates from it cleanly. On a dark
suit against a dark backdrop the mask collapsed to the shirt alone (~7% of
frame) and inverting produced a photo negative; the plain dither reads
correctly in both themes, so both variants share one ink map and differ only
in colour. Revisit if you shoot against a flat light background.
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
PAL = CFG["palette"]

GW, GH = 300, 340          # dot grid
CONTRAST = 1.3             # 2.4x reads harsh and skull-like
UNSHARP = (3, 140, 3)      # radius, percent, threshold
TARGET_MEAN = 138          # post-lift midtone; the one knob worth tuning per photo


def prep(path):
    """Crop to head+shoulders aspect, lift exposure, sharpen."""
    im = Image.open(path).convert("RGB")
    target = GW / GH
    w, h = im.size
    if w / h > target:                     # too wide - trim the sides
        nw = int(h * target)
        im = im.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
    else:                                  # too tall - keep the top (head+shoulders)
        nh = int(w / target)
        im = im.crop((0, 0, w, nh))
    im = im.resize((GW, GH), Image.LANCZOS)

    g = ImageOps.autocontrast(im.convert("L"), cutoff=1)

    # A dark subject on a dark backdrop still averages ~66 after autocontrast,
    # which dithers to ~75% ink and reads as a black blob. Gamma-lift midtones.
    a = np.asarray(g, dtype=np.float32) / 255.0
    gamma = np.log(TARGET_MEAN / 255.0) / np.log(max(a.mean(), 1e-3))
    g = Image.fromarray((np.clip(a ** gamma, 0, 1) * 255).astype(np.uint8))

    g = ImageEnhance.Contrast(g).enhance(CONTRAST)
    return g.filter(ImageFilter.UnsharpMask(*UNSHARP))


def dither(gray):
    """PIL's convert('1') is Floyd-Steinberg error diffusion. True = ink."""
    return ~np.asarray(gray.convert("1"), dtype=bool)


def runs_to_path(ink):
    """Row-wise run-length encode into one path 'd'. One element, one fill."""
    d = []
    for y in range(ink.shape[0]):
        row = ink[y]
        x = 0
        while x < ink.shape[1]:
            if not row[x]:
                x += 1
                continue
            start = x
            while x < ink.shape[1] and row[x]:
                x += 1
            d.append(f"M{start} {y}h{x - start}v1h{-(x - start)}Z")
    return "".join(d), len(d)


def svg(ink, colour, bg):
    d, n = runs_to_path(ink)
    plate = "" if bg is None else f'<rect width="{GW}" height="{GH}" rx="6" fill="{bg}"/>'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{GW}" height="{GH}" '
        f'viewBox="0 0 {GW} {GH}" shape-rendering="crispEdges">'
        f"{plate}"
        "<style>@keyframes fi{from{opacity:0}to{opacity:1}}"
        "#p{opacity:0;animation:fi 1.8s ease-out .2s forwards}"
        "@media (prefers-reduced-motion:reduce){#p{animation:none;opacity:1}}</style>"
        f'<path id="p" d="{d}" fill="{colour}"/></svg>'
    ), n


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: make_portrait_svg.py <photo>")
    photo = pathlib.Path(sys.argv[1])
    if not photo.exists():
        sys.exit(f"no such file: {photo}")

    ink = dither(prep(photo))

    for fname, colour, bg in (
        ("portrait-light.svg", PAL["chrome"], None),
        ("portrait-dark.svg", PAL["portrait"], PAL["bg"]),
    ):
        body, n = svg(ink, colour, bg)
        (ROOT / fname).write_text(body, encoding="utf-8")
        print(f"{fname}: {n} runs, {(ROOT / fname).stat().st_size // 1024} KB")

    cov = ink.mean()
    print(f"ink coverage: {cov:.1%}")
    if not 0.10 <= cov <= 0.60:
        print(f"WARNING: coverage outside 10-60% - tune TARGET_MEAN (now {TARGET_MEAN})")


if __name__ == "__main__":
    main()
