"""Render contributions.json as an animated 53-week heatmap SVG.

Reveal is a diagonal wipe driven by (week + day) so it sweeps top-left to
bottom-right, plays once, and freezes. No loop - a looping glow on a profile
page is noise.
"""
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
PAL = CFG["palette"]

BOX, GAP = 11, 3
PITCH = BOX + GAP
PAD_L, PAD_T = 30, 22
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# index 0 is the empty cell. Against a dark card it must stay visible -
# near-black here makes the whole grid look broken.
LEVELS = ["#1B2333", "#0E4429", "#006D32", "#26A641", "#39D353"]

STEP = 0.012   # seconds of delay per diagonal
DUR = 0.45


def grid(days):
    """Bucket days into (week, weekday) columns the way GitHub lays them out."""
    first = dt.date.fromisoformat(days[0]["date"])
    origin = first - dt.timedelta(days=first.weekday() + 1 if first.weekday() != 6 else 0)
    cells = []
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        offset = (date - origin).days
        cells.append((offset // 7, offset % 7, d))
    return cells


def month_labels(cells):
    seen, out = set(), []
    for week, day, d in cells:
        date = dt.date.fromisoformat(d["date"])
        if date.month not in seen and date.day <= 7 and day == 0:
            seen.add(date.month)
            out.append((week, MONTHS[date.month - 1]))
    return out


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(data):
    cells = grid(data["days"])
    weeks = max(c[0] for c in cells) + 1
    w = PAD_L + weeks * PITCH + 20
    h = PAD_T + 7 * PITCH + 52

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="ui-monospace,SFMono-Regular,Menlo,monospace">',
        f'<rect width="{w}" height="{h}" rx="10" fill="{PAL["bg"]}"/>',
        "<style>",
        "@keyframes pop{from{opacity:0;transform:translateY(-6px) scale(.4)}"
        "to{opacity:1;transform:none}}",
        ".c{opacity:0;animation:pop %.2fs ease-out forwards;transform-box:fill-box;"
        "transform-origin:center}" % DUR,
        "@media (prefers-reduced-motion:reduce){.c{animation:none;opacity:1}}",
        "</style>",
    ]

    for week, label in month_labels(cells):
        x = PAD_L + week * PITCH
        parts.append(f'<text x="{x}" y="{PAD_T - 8}" font-size="10" '
                     f'fill="{PAL["muted"]}">{label}</text>')

    for i, lbl in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = PAD_T + i * PITCH + BOX - 2
        parts.append(f'<text x="0" y="{y}" font-size="9" fill="{PAL["muted"]}">{lbl}</text>')

    for week, day, d in cells:
        x = PAD_L + week * PITCH
        y = PAD_T + day * PITCH
        delay = (week + day) * STEP
        parts.append(
            f'<rect class="c" x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2.5" '
            f'fill="{LEVELS[min(d["level"], 4)]}" style="animation-delay:{delay:.2f}s">'
            f'<title>{d["count"]} on {d["date"]}</title></rect>'
        )

    fy = PAD_T + 7 * PITCH + 22
    parts.append(f'<text x="{PAD_L}" y="{fy}" font-size="11" fill="{PAL["text"]}">'
                 f'{data["total"]:,} contributions in the last year</text>')
    parts.append(f'<text x="{PAD_L}" y="{fy + 16}" font-size="10" fill="{PAL["muted"]}">'
                 f'current streak {data["current_streak"]}d  &#183;  '
                 f'longest {data["longest_streak"]}d  &#183;  '
                 f'best {data["best_day"]["count"]} on {esc(data["best_day"]["date"])}</text>')

    lx = w - 150
    parts.append(f'<text x="{lx}" y="{fy}" font-size="10" fill="{PAL["muted"]}">Less</text>')
    for i, col in enumerate(LEVELS):
        parts.append(f'<rect x="{lx + 30 + i * 14}" y="{fy - 9}" width="{BOX}" '
                     f'height="{BOX}" rx="2.5" fill="{col}"/>')
    parts.append(f'<text x="{lx + 30 + 5 * 14 + 4}" y="{fy}" font-size="10" '
                 f'fill="{PAL["muted"]}">More</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def _selfcheck():
    """Grid maths is the only thing here that can silently go wrong."""
    days = [{"date": (dt.date(2025, 1, 5) + dt.timedelta(days=i)).isoformat(),
             "level": i % 5, "count": i} for i in range(371)]
    cells = grid(days)
    assert len(cells) == 371, len(cells)
    assert all(0 <= day <= 6 for _, day, _ in cells)
    # 2025-01-05 is a Sunday, so it must land in row 0 of week 0
    assert cells[0][:2] == (0, 0), cells[0][:2]
    # consecutive days never share a (week, day) slot
    assert len({(w, d) for w, d, _ in cells}) == 371
    print("selfcheck ok")


def main():
    if "--selfcheck" in sys.argv:
        return _selfcheck()
    src = ROOT / "data" / "contributions.json"
    if not src.exists():
        sys.exit("Run fetch_contributions.py first.")
    data = json.loads(src.read_text(encoding="utf-8"))
    out = ROOT / "contrib-heatmap.svg"
    out.write_text(render(data), encoding="utf-8")
    print(f"wrote {out.name} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
