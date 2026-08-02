"""Photo -> 1-bit dithered dot portrait as SVG (dark + light variants).

The reference pipeline used rembg + OpenCV for background segmentation. Both
are heavy CPU installs; scipy.ndimage does the same closing/fill/largest-
component work and is already a dependency, so neither is needed here.

Dots are emitted as run-length <path> segments with shape-rendering=crispEdges.
Font glyphs mush below ~2px - that is why this is not ASCII art.

    python make_portrait_svg.py photo.jpg
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from scipy import ndimage

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
PAL = CFG["palette"]

GW, GH = 300, 340          # dot grid
CONTRAST = 1.3             # 2.4x reads harsh and skull-like
UNSHARP = (3, 140, 3)      # radius, percent, threshold


def prep(path):
    """Crop to head+shoulders aspect, then boost local contrast."""
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
    g = ImageEnhance.Contrast(g).enhance(CONTRAST)
    return g.filter(ImageFilter.UnsharpMask(*UNSHARP))


def subject_mask(gray):
    """Background = the bright region connected to the border. Needs a flat backdrop."""
    a = np.asarray(gray, dtype=np.float32)
    thresh = np.percentile(a, 82)
    fg = a < thresh

    fg = ndimage.binary_closing(fg, structure=np.ones((5, 5)))
    fg = ndimage.binary_fill_holes(fg)

    lab, n = ndimage.label(fg)
    if n == 0:
        return np.ones_like(fg, dtype=bool)
    sizes = ndimage.sum(fg, lab, range(1, n + 1))
    keep = int(np.argmax(sizes)) + 1
    mask = lab == keep
    # dilate slightly so error-diffusion bleed at the edge is not clipped mid-face
    return ndimage.binary_dilation(mask, structure=np.ones((3, 3)), iterations=2)


def dither(gray):
    """PIL's convert('1') is Floyd-Steinberg error diffusion. True = ink."""
    return np.asarray(gray.convert("1"), dtype=bool) == False  # noqa: E712


def runs_to_path(ink):
    """Row-wise run-length encode into one path 'd'. One element, one fill."""
    d, count = [], 0
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
            count += 1
    return "".join(d), count


def svg(ink, colour, bg):
    d, n = runs_to_path(ink)
    body = "" if bg is None else f'<rect width="{GW}" height="{GH}" fill="{bg}"/>'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{GW}" height="{GH}" '
        f'viewBox="0 0 {GW} {GH}" shape-rendering="crispEdges">'
        f"{body}"
        "<style>@keyframes fi{from{opacity:0}to{opacity:1}}"
        "#p{opacity:0;animation:fi 2s ease-out .2s forwards}"
        "@media (prefers-reduced-motion:reduce){#p{animation:none;opacity:1}}</style>"
        f'<path id="p" d="{d}" fill="{colour}"/></svg>'
    ), n


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: make_portrait_svg.py <photo>")
    photo = pathlib.Path(sys.argv[1])
    if not photo.exists():
        sys.exit(f"no such file: {photo}")

    gray = prep(photo)
    ink = dither(gray)

    # light: keep the background, dots draw the dark parts of the photo
    light, n1 = svg(ink, PAL["chrome"], None)
    (ROOT / "portrait-light.svg").write_text(light, encoding="utf-8")

    # dark: drop the background so dots draw only the lit subject,
    # otherwise it reads as a photo negative
    dark_ink = ink & subject_mask(gray)
    dark, n2 = svg(dark_ink, PAL["portrait"], PAL["bg"])
    (ROOT / "portrait-dark.svg").write_text(dark, encoding="utf-8")

    for f, n in (("portrait-light.svg", n1), ("portrait-dark.svg", n2)):
        kb = (ROOT / f).stat().st_size // 1024
        print(f"{f}: {n} runs, {kb} KB")
    print(f"ink coverage: light {ink.mean():.1%}  dark {dark_ink.mean():.1%}")
    if not 0.10 <= ink.mean() <= 0.55:
        print("WARNING: coverage outside 10-55% - photo is likely too flat or too dark")


if __name__ == "__main__":
    main()
