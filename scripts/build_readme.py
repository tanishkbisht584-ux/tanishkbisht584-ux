"""Generate README.md from config.json so the username lives in exactly one place.

Sections whose config is missing are omitted rather than emitted broken - a
half-filled URL renders as a broken-image icon on your profile.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
U = CFG["username"]
PAL = CFG["palette"]
RAW = f"https://raw.githubusercontent.com/{U}/{U}"
BG = PAL["bg"].lstrip("#")
CH = PAL["chrome"].lstrip("#")
AC = PAL["accent"].lstrip("#")
MU = PAL["muted"].lstrip("#")
TX = PAL["text"].lstrip("#")


def portrait():
    """'ascii' for the character portrait, 'dots' for the dithered one."""
    stem = "ascii" if CFG.get("portrait_style", "ascii") == "ascii" else "portrait"
    if not (ROOT / f"{stem}-dark.svg").exists():
        return ""
    return f"""<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{RAW}/main/{stem}-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="{RAW}/main/{stem}-light.svg">
  <img alt="{CFG['name']}" src="{RAW}/main/{stem}-light.svg" width="370">
</picture>"""


def header():
    # the terminal card fills the gap under the header card, since the portrait
    # column is the taller of the two
    right = '<img src="./info-card.svg" width="490" alt="info" />'
    if (ROOT / "terminal-card.svg").exists():
        right += '\n<br>\n<img src="./terminal-card.svg" width="490" alt="session" />'
    p = portrait()
    if not p:
        return right
    return f"""<table>
  <tr>
    <td valign="top">{p}</td>
    <td valign="top">{right}</td>
  </tr>
</table>"""


def stats():
    inst = CFG.get("stats_instance", "").strip().rstrip("/")
    streak = (f"https://streak-stats.demolab.com/?user={U}&hide_border=true"
              f"&background={BG}&stroke={CH}&ring={PAL['portrait'].lstrip('#')}"
              f"&fire={AC}&currStreakLabel={CH}&sideLabels={MU}"
              f"&currStreakNum={TX}&sideNums={TX}&dates={MU}"
              f"&titleColor={CH}&card_width=1180")
    out = [f'<img width="100%" src="{streak}" alt="streak" />']
    if inst:
        if not inst.startswith("http"):
            inst = "https://" + inst
        common = (f"hide_border=true&title_color={CH}&text_color={MU}"
                  f"&bg_color={BG}&card_width=500")
        out.append("<br/>")
        out.append(f'<img width="49%" src="{inst}/api?username={U}&show_icons=true'
                   f'&count_private=true&include_all_commits=true&hide_rank=true'
                   f'&icon_color={PAL["portrait"].lstrip("#")}&{common}" alt="stats" />')
        out.append(f'<img width="49%" src="{inst}/api/top-langs/?username={U}'
                   f'&layout=compact&langs_count=8&{common}" alt="top langs" />')
    return "\n".join(out)


def badges():
    items = []
    if CFG.get("linkedin"):
        # shields.io bug: the LinkedIn glyph only renders on brand blue #0A66C2
        items.append(f'<a href="{CFG["linkedin"]}"><img src="https://img.shields.io/badge/'
                     f'LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" '
                     f'alt="LinkedIn" /></a>')
    if CFG.get("instagram"):
        items.append(f'<a href="{CFG["instagram"]}"><img src="https://img.shields.io/badge/'
                     f'Instagram-{BG}?style=for-the-badge&logo=instagram'
                     f'&logoColor={PAL["portrait"].lstrip("#")}&labelColor={BG}" '
                     f'alt="Instagram" /></a>')
    if CFG.get("portfolio"):
        items.append(f'<a href="{CFG["portfolio"]}"><img src="https://img.shields.io/badge/'
                     f'Portfolio-{BG}?style=for-the-badge&logo=vercel'
                     f'&logoColor={CH}&labelColor={BG}" alt="Portfolio" /></a>')
    if CFG.get("email"):
        items.append(f'<a href="mailto:{CFG["email"]}"><img src="https://img.shields.io/badge/'
                     f'Email-{BG}?style=for-the-badge&logo=gmail'
                     f'&logoColor={AC}&labelColor={BG}" alt="Email" /></a>')
    return "\n&nbsp;&nbsp;\n".join(items)


def main():
    snake = f"""<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{RAW}/output/github-snake-dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="{RAW}/output/github-snake.svg" />
  <img alt="Snake eating my contributions" src="{RAW}/output/github-snake.svg" />
</picture>"""

    md = f"""<div align="center">

### <code>{U}@github ~ $ whoami</code>

{header()}

<br><br>

### <code>{U}@github ~ $ cat stack.txt</code>

<img src="./skills-card.svg" width="880" alt="skills" />

<br><br>

### <code>{U}@github ~ $ ./contributions.sh</code>

<img src="./contrib-heatmap.svg" width="860" alt="contribution heatmap" />

<br><br>

{snake}

<br><br>

### <code>{U}@github ~ $ git log --stat</code>

{stats()}

<br><br>

{badges()}

</div>
"""
    (ROOT / "README.md").write_text(md, encoding="utf-8")
    print("wrote README.md")
    if not CFG.get("stats_instance"):
        print("note: stats_instance empty - stats/top-langs cards omitted")
    if not (ROOT / "portrait-dark.svg").exists():
        print("note: no portrait yet - run make_portrait_svg.py <photo>")


if __name__ == "__main__":
    main()
