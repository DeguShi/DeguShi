"""Build assets/profile.svg from live GitHub data plus the hand-written content."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Callable

from card.compose import compose, header, spine
from card.content import BUILDING_TOPICS, RESEARCH_TOPICS, TERMINAL
from card.data import Stats, fetch_stats
from card.graph import render_graph
from card.stats import render_stats
from card.terminal import render_terminal
from card.theme import section_header

log = logging.getLogger("build")
SECTION_GAP = 56


def sections(stats: Stats) -> list[tuple[str, str, Callable[[int], tuple[str, int, str]]]]:
    """(index, title, renderer) per section; each renderer returns (svg, height, css)."""
    return [
        ("01", "shell", lambda top: (*render_terminal(TERMINAL, top, t0=1.4), "")),
        ("02", "research ⟷ building", lambda top: render_graph(RESEARCH_TOPICS, BUILDING_TOPICS, top)),
        ("03", "activity", lambda top: (*render_stats(stats, top), "")),
    ]


def render(login: str, token: str) -> str:
    """Lay the sections out top to bottom and return the finished SVG."""
    stats = fetch_stats(login, token)
    parts, css, marks, y = [header()], [], [], 196
    for idx, title, make in sections(stats):
        marks.append(y)
        parts.append(section_header(y, idx, title))
        svg, h, extra = make(y + 22)
        parts.append(svg)
        css.append(extra)
        y += 22 + h + SECTION_GAP
    parts.insert(0, spine(marks, y - 20))
    return compose("".join(parts), y + 10, "".join(css))


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
    svg = render(args.login, token)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg, encoding="utf-8")
    log.info(f"wrote {args.out} ({len(svg) / 1024:.0f} KiB)")


if __name__ == "__main__":
    main()
