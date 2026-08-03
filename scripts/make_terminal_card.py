"""Looping terminal-session card that types itself out.

Sits under the header card, filling the space beside the taller portrait.

Each line gets its own @keyframes with the reveal offset baked in as a
percentage of one shared loop duration. That is why the whole sequence stays in
sync: twelve independent animations of equal length, differing only in when
their reveal happens. Driving it off one parent animation would need SMIL
begin-chaining, which GitHub renders inconsistently inside <img>.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
PAL = CFG["palette"]

W = 512
FS = 12
ROW = 19
PAD = 18
BAR = 30
LOOP = 15.0        # seconds for one full pass
TYPE = 0.45        # seconds a line takes to type
HOLD = 2.4         # seconds everything stays up before clearing

# kind: cmd (prompt + command), ok, wait, out
LINES = [
    ("cmd", "whoami"),
    ("out", "tanishk - quant developer / ai engineer"),
    ("cmd", "market-agent --status"),
    ("ok", "backtest engine      ready"),
    ("ok", "paper broker         connected"),
    ("wait", "live execution       in progress"),
    ("cmd", "git log --oneline -1"),
    ("out", "feat: multi-agent trading platform"),
    ("cmd", "cat mission.txt"),
    ("out", "building AI for financial markets"),
]


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build():
    h = PAD * 2 + BAR + len(LINES) * ROW + 8
    step = (LOOP - HOLD) / (len(LINES) + 1)

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
         f'viewBox="0 0 {W} {h}" '
         f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace">',
         f'<rect width="{W}" height="{h}" rx="10" fill="{PAL["bg"]}" '
         f'stroke="{PAL["chrome"]}" stroke-opacity=".35"/>',
         f'<line x1="0" y1="{BAR}" x2="{W}" y2="{BAR}" '
         f'stroke="{PAL["chrome"]}" stroke-opacity=".2"/>']

    for i, col in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        p.append(f'<circle cx="{PAD + i * 16}" cy="{BAR / 2}" r="5" fill="{col}"/>')
    p.append(f'<text x="{PAD + 58}" y="{BAR / 2 + 4}" font-size="11" '
             f'fill="{PAL["muted"]}">session -- {esc(CFG["username"])}</text>')

    style = ["<style>"]
    for i in range(len(LINES)):
        a = i * step / LOOP * 100                 # reveal starts
        b = (i * step + TYPE) / LOOP * 100        # reveal done
        end = (LOOP - HOLD / 2) / LOOP * 100      # clear for the next pass
        style.append(
            f"@keyframes t{i}{{"
            f"0%,{a:.2f}%{{clip-path:inset(0 100% 0 0)}}"
            f"{b:.2f}%,{end:.2f}%{{clip-path:inset(0 0 0 0)}}"
            f"100%{{clip-path:inset(0 100% 0 0)}}}}"
            f".t{i}{{clip-path:inset(0 100% 0 0);"
            f"animation:t{i} {LOOP}s steps(28,end) infinite}}"
        )
    # cursor rides below the last line
    style.append("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
                 ".cur{animation:blink 1s step-end infinite}")
    style.append("@media (prefers-reduced-motion:reduce){"
                 "[class^=t]{animation:none;clip-path:none}"
                 ".cur{animation:none}}")
    style.append("</style>")
    p += style

    y = BAR + PAD + FS
    for i, (kind, text) in enumerate(LINES):
        p.append(f'<g class="t{i}">')
        if kind == "cmd":
            p.append(f'<text x="{PAD}" y="{y}" font-size="{FS}" '
                     f'fill="{PAL["accent"]}">$</text>')
            p.append(f'<text x="{PAD + 14}" y="{y}" font-size="{FS}" '
                     f'fill="{PAL["text"]}">{esc(text)}</text>')
        elif kind in ("ok", "wait"):
            mark, col = (("[ok]", PAL["accent"]) if kind == "ok"
                         else ("[..]", PAL["chrome"]))
            p.append(f'<text x="{PAD + 14}" y="{y}" font-size="{FS}" '
                     f'fill="{col}">{mark}</text>')
            p.append(f'<text x="{PAD + 52}" y="{y}" font-size="{FS}" '
                     f'fill="{PAL["muted"]}">{esc(text)}</text>')
        else:
            p.append(f'<text x="{PAD + 14}" y="{y}" font-size="{FS}" '
                     f'fill="{PAL["muted"]}">{esc(text)}</text>')
        p.append("</g>")
        y += ROW

    p.append(f'<text class="cur" x="{PAD}" y="{y}" font-size="{FS}" '
             f'fill="{PAL["accent"]}">$ _</text>')
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    out = ROOT / "terminal-card.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB, "
          f"{len(LINES)} lines, {LOOP}s loop)")
