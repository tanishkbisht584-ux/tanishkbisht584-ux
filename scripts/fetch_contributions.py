"""Scrape the public contribution calendar. No token, no API, no rate limit."""
import json
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
URL = "https://github.com/users/{}/contributions"


def fetch(username):
    r = requests.get(
        URL.format(username),
        headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"},
        timeout=30,
    )
    r.raise_for_status()
    return r.text


def parse(html):
    soup = BeautifulSoup(html, "html.parser")

    # Counts live in <tool-tip for="cell-id">N contributions on ...</tool-tip>,
    # not on the cell itself. Map them back by id.
    counts = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if not target:
            continue
        m = re.match(r"(\d+|No)\s+contribution", tip.get_text(strip=True))
        if m:
            counts[target] = 0 if m.group(1) == "No" else int(m.group(1))

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue  # padding cells at the start/end of the grid
        days.append({
            "date": date,
            "level": int(td.get("data-level", 0)),
            "count": counts.get(td.get("id"), 0),
        })
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    """Current streak counts back from the last day that could still be extended."""
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    current = 0
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        elif current or d is not days[-1]:
            break  # today being empty doesn't break a streak that ended yesterday
    return current, longest


def main():
    user = CFG["username"]
    if user == "REPLACE_ME":
        sys.exit("Set 'username' in config.json first.")

    days = parse(fetch(user))
    if not days:
        sys.exit("Parsed 0 days - GitHub markup may have changed.")

    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    out = {
        "username": user,
        "days": days,
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
    }

    dest = ROOT / "data"
    dest.mkdir(exist_ok=True)
    (dest / "contributions.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{len(days)} days, {out['total']} contributions, streak {current} (best {longest})")


if __name__ == "__main__":
    main()
