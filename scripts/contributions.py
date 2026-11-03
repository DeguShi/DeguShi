"""Render the last year of GitHub contributions as an animated SVG."""

from __future__ import annotations

import argparse
import json
import logging
import os
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

log = logging.getLogger("contributions")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""



@dataclass(frozen=True)
class Style:
    cell: int = 13
    gap: int = 4
    left: int = 40
    top: int = 74
    width: int = 960
    height: int = 222
    palette: tuple[str, ...] = ("#221f2c", "#6e3047", "#b8434f", "#f06a4b", "#ffb36b")
    scan: str = "#2DD4BF"
    sweep_s: float = 7.0


@dataclass(frozen=True)
class Day:
    day: date
    count: int
    level: int


def fetch_calendar(login: str, token: str) -> tuple[int, list[list[Day]]]:
    """Fetch the contribution calendar via the GitHub GraphQL API."""
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload['errors']}")
    cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    raw = [[(date.fromisoformat(d["date"]), d["contributionCount"]) for d in w["contributionDays"]]
           for w in cal["weeks"]]
    cuts = level_cuts([c for w in raw for _, c in w])
    weeks = [[Day(d, c, sum(c >= t for t in cuts) if c else 0) for d, c in w] for w in raw]
    return cal["totalContributions"], weeks


def level_cuts(counts: list[int]) -> list[int]:
    """Thresholds for levels 1-4: quartiles of the non-zero days, so one outlier can't flatten the scale."""
    nz = sorted(c for c in counts if c)
    if not nz:
        return [1, 1, 1, 1]
    return [1] + [nz[min(len(nz) - 1, int(len(nz) * q))] for q in (0.25, 0.5, 0.75)]


def render_cells(weeks: list[list[Day]], s: Style) -> str:
    """One rounded rect per day; each column brightens as the scan line passes it."""
    step = s.cell + s.gap
    out: list[str] = []
    for col, week in enumerate(weeks):
        delay = s.sweep_s * col / len(weeks)
        for day in week:
            x = s.left + col * step
            y = s.top + day.day.isoweekday() % 7 * step
            cls = "c lit" if day.level else "c"
            out.append(
                f'<rect class="{cls}" x="{x}" y="{y}" width="{s.cell}" height="{s.cell}" rx="3" '
                f'fill="{s.palette[day.level]}" style="animation-delay:{delay:.2f}s">'
                f"<title>{day.count} on {day.day.isoformat()}</title></rect>"
            )
    return "\n".join(out)


def render_months(weeks: list[list[Day]], s: Style) -> str:
    """Month labels above the first column in which each month starts."""
    step = s.cell + s.gap
    out: list[str] = []
    seen: int | None = None
    for col, week in enumerate(weeks):
        month = week[0].day.month
        if month != seen and col < len(weeks) - 2:
            x = s.left + col * step
            out.append(f'<text class="m" x="{x}" y="{s.top - 10}">{week[0].day.strftime("%b").lower()}</text>')
            seen = month
    return "\n".join(out)


def render_svg(total: int, weeks: list[list[Day]], s: Style) -> str:
    """Assemble the full SVG document."""
    step = s.cell + s.gap
    grid_w = len(weeks) * step - s.gap
    scan_y, scan_h = s.top - 6, 7 * step + 8
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.width} {s.height}" width="{s.width}" height="{s.height}" role="img" aria-label="{total} GitHub contributions in the last year">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#14121c"/><stop offset="1" stop-color="#1b1826"/></linearGradient>
<linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="{s.scan}" stop-opacity="0"/><stop offset=".85" stop-color="{s.scan}" stop-opacity=".18"/><stop offset="1" stop-color="{s.scan}" stop-opacity=".9"/></linearGradient>
<style>
.t {{ font: 600 15px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; fill: #f2efe9; }}
.k {{ font: 12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; fill: #8a849c; }}
.m {{ font: 11px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; fill: #6f6982; }}
.c {{ transform-box: fill-box; transform-origin: center; animation: pop {s.sweep_s}s ease-out infinite; }}
.c.lit {{ animation-name: glow; }}
@keyframes pop {{ 0% {{ transform: scale(1); }} 3% {{ transform: scale(.7); }} 8%, 100% {{ transform: scale(1); }} }}
@keyframes glow {{ 0% {{ transform: scale(1); filter: brightness(1); }} 3% {{ transform: scale(1.35); filter: brightness(1.6); }} 12%, 100% {{ transform: scale(1); filter: brightness(1); }} }}
.beam {{ animation: sweep {s.sweep_s}s linear infinite; }}
@keyframes sweep {{ from {{ transform: translateX(0); }} to {{ transform: translateX({grid_w}px); }} }}
</style>
</defs>
<rect x=".5" y=".5" width="{s.width - 1}" height="{s.height - 1}" rx="16" fill="url(#bg)" stroke="#2a2636"/>
<text class="t" x="{s.left}" y="36">{total:,} contributions</text>
<text class="k" x="{s.left + grid_w}" y="36" text-anchor="end">last 12 months · updated daily</text>
{render_months(weeks, s)}
{render_cells(weeks, s)}
<clipPath id="grid"><rect x="{s.left - 2}" y="{scan_y}" width="{grid_w + 4}" height="{scan_h}"/></clipPath>
<g clip-path="url(#grid)"><rect class="beam" x="{s.left - 60}" y="{scan_y}" width="60" height="{scan_h}" rx="3" fill="url(#beam)"/></g>
</svg>
"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--login", required=True, help="GitHub username")
    p.add_argument("--out", type=Path, required=True, help="output SVG path")
    p.add_argument("--token-env", default="GITHUB_TOKEN", help="env var holding the API token")
    return p.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    token = os.environ.get(args.token_env)
    if not token:
        raise SystemExit(f"missing token in ${args.token_env}")
    total, weeks = fetch_calendar(args.login, token)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_svg(total, weeks, Style()), encoding="utf-8")
    log.info(f"wrote {args.out} ({total} contributions, {len(weeks)} weeks)")


if __name__ == "__main__":
    main()
