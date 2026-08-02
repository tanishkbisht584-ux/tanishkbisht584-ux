"""Neofetch-style info card. Rows fade in on a stagger so the panel 'prints'.

Values are locked with textLength so they stay right-aligned regardless of
which monospace font the browser actually resolves.
"""
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
PAL = CFG["palette"]

W, H = 490, 340
PAD = 20
ROW = 23
FS = 14
STATIC = os.environ.get("STATIC") == "1"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def rows():
    """Empty config values are dropped - a blank row reads as a rendering bug."""
    c = CFG

    def block(*pairs):
        return [(k, c.get(v, "")) for k, v in pairs if str(c.get(v, "")).strip()]

    groups = [
        block(("Subject", "name"), ("Role", "role"), ("Origin", "location"),
              ("Education", "education"), ("Status", "status"), ("ToolChain", "toolchain")),
        block(("Core.Lang", "languages"), ("Core.Frontend", "frontend"),
              ("Core.Backend", "backend"), ("Core.Database", "database"),
              ("Core.Infra", "infra")),
        block(("Grid.Mail", "email"), ("Grid.Portfolio", "portfolio"),
              ("Grid.LinkedIn", "linkedin")),
    ]

    out = []
    for g in (g for g in groups if g):
        if out:
            out.append((None, None))   # spacer between populated groups only
        out += g
    return out


def build():
    body = rows()
    h = PAD * 2 + 34 + len(body) * ROW + 10
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">',
        f'<rect width="{W}" height="{h}" rx="10" fill="{PAL["bg"]}" '
        f'stroke="{PAL["chrome"]}" stroke-opacity=".25"/>',
    ]
    if not STATIC:
        p += ["<style>",
              "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}",
              ".r{opacity:0;animation:in .4s ease-out forwards}",
              "@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1}}",
              "</style>"]

    p.append(f'<text x="{PAD}" y="{PAD + 14}" font-size="13" fill="{PAL["chrome"]}">'
             f'{esc(CFG["username"])}@github</text>')
    p.append(f'<line x1="{PAD}" y1="{PAD + 22}" x2="{W - PAD}" y2="{PAD + 22}" '
             f'stroke="{PAL["chrome"]}" stroke-opacity=".3"/>')

    y = PAD + 34 + FS
    for i, (key, val) in enumerate(body):
        cls = "" if STATIC else f' class="r" style="animation-delay:{0.06 * i + 0.2:.2f}s"'
        if key is None:
            y += ROW
            continue
        p.append(f'<g{cls}>')
        p.append(f'<text x="{PAD}" y="{y}" font-size="{FS}" fill="{PAL["accent"]}">{esc(key)}</text>')
        # right-aligned value, width-locked so it never drifts
        p.append(f'<text x="{W - PAD}" y="{y}" font-size="{FS}" fill="{PAL["muted"]}" '
                 f'text-anchor="end">{esc(val)}</text>')
        p.append("</g>")
        y += ROW

    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    out = ROOT / "info-card.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")
