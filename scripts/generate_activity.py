#!/usr/bin/env python3
"""Generate a themed contribution-heatmap SVG from commit dates.

Usage:
    generate_activity.py --dates-json dates.json --out activity.svg
    generate_activity.py --out activity.svg        # uses `gh api` (GitHub Actions)

Theme: dark card (#0d1117), red scale, gold highlights — matches profile banner.
"""
import json
import os
import subprocess
import sys
import datetime

OWNER = os.environ.get("GH_OWNER", "pvt-harsh")
REPOS = ["Meta-Track", "pvt-harsh"]
WEEKS = 26

# Theme
BG = "#0d1117"
BORDER = "#30363d"
GOLD = "#E8B84B"
RED = "#ff4d4d"
GRAY = "#8b949e"
EMPTY = "#161b22"
SCALE = ["#161b22", "#7f1d1d", "#b91c1c", "#ef4444", "#E8B84B"]  # 0,1,2,3,4+

CELL, GAP = 12, 4
STEP = CELL + GAP
PAD_L, PAD_R, PAD_T, PAD_B = 36, 18, 66, 40
GRID_W = WEEKS * STEP - GAP
GRID_H = 7 * STEP - GAP
WIDTH = PAD_L + GRID_W + PAD_R
HEIGHT = PAD_T + GRID_H + PAD_B


def fetch_dates_gh():
    dates = []
    for repo in REPOS:
        out = subprocess.run(
            ["gh", "api", f"repos/{OWNER}/{repo}/commits", "--paginate",
             "-q", ".[].commit.author.date"],
            capture_output=True, text=True, check=False)
        dates += [d for d in out.stdout.split() if d.strip()]
    return dates


def level(count):
    return 0 if count == 0 else min(count, 4)


def main():
    if "--dates-json" in sys.argv:
        dates = json.load(open(sys.argv[sys.argv.index("--dates-json") + 1]))
    else:
        dates = fetch_dates_gh()
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "activity.svg"

    counts = {}
    for d in dates:
        day = d[:10]
        counts[day] = counts.get(day, 0) + 1
    total = sum(counts.values())

    today = datetime.date.today()
    # End on the most recent Saturday (GitHub-style weeks run Sun-Sat)
    end = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    start = end - datetime.timedelta(days=WEEKS * 7 - 1)
    # Align start back to a Sunday
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)

    parts = []
    month_seen = {}
    for w in range(WEEKS):
        for d in range(7):
            day = start + datetime.timedelta(days=w * 7 + d)
            future = day > today
            c = 0 if future else counts.get(day.isoformat(), 0)
            x = PAD_L + w * STEP
            y = PAD_T + d * STEP
            fill = EMPTY if future else SCALE[level(c)]
            op = ' opacity="0.25"' if future else ""
            label = day.strftime("%b %d, %Y")
            tip = f"{c} contribution{'s' if c != 1 else ''} on {label}" if not future else label
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5"'
                f' fill="{fill}"{op}><title>{tip}</title></rect>')
        # Month label when the month changes at this column
        m = (start + datetime.timedelta(days=w * 7)).strftime("%b")
        if m not in month_seen:
            month_seen[m] = True
            parts.append(
                f'<text x="{PAD_L + w * STEP}" y="{PAD_T - 10}" fill="{GRAY}"'
                f' font-size="10" font-family="monospace">{m}</text>')

    # Day labels (Mon / Wed / Fri)
    for d, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="6" y="{PAD_T + d * STEP + 10}" fill="{GRAY}"'
            f' font-size="10" font-family="monospace">{name}</text>')

    # Legend
    lx = WIDTH - PAD_R - 150
    ly = PAD_T + GRID_H + 22
    legend = [f'<text x="{lx}" y="{ly + 9}" fill="{GRAY}" font-size="10"'
              f' font-family="monospace">Less</text>']
    for i, col in enumerate(SCALE):
        legend.append(
            f'<rect x="{lx + 38 + i * 16}" y="{ly}" width="{CELL}" height="{CELL}"'
            f' rx="2.5" fill="{col}"/>')
    legend.append(
        f'<text x="{lx + 38 + 5 * 16 + 6}" y="{ly + 9}" fill="{GRAY}"'
        f' font-size="10" font-family="monospace">More</text>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>
<text x="18" y="30" fill="{GOLD}" font-size="15" font-weight="bold" font-family="monospace">Contribution Activity</text>
<text x="18" y="48" fill="{GRAY}" font-size="11" font-family="monospace">{total} contributions in the last {WEEKS} weeks</text>
{''.join(parts)}
{''.join(legend)}
</svg>
"""
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out} ({total} contributions)")


if __name__ == "__main__":
    main()
