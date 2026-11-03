"""Section: headline tiles, animated contribution grid, language mix."""

from __future__ import annotations

from card.data import Day, Stats
from card.theme import AMBER, CORAL, FAINT, INK, LINE, MINT, SKY, VIOLET, WIDTH, esc

CELL, GAP = 12, 4
GRID_PALETTE = ("#221f2c", "#6e3047", "#b8434f", "#f06a4b", "#ffb36b")
LANG_COLOURS = (MINT, CORAL, AMBER, VIOLET, SKY)
SWEEP_S = 7.0


def level_cuts(days: list[Day]) -> list[int]:
    """Level thresholds from quartiles of active days, so one outlier can't flatten the scale."""
    nz = sorted(d.count for d in days if d.count)
    if not nz:
        return [1, 1, 1, 1]
    return [1] + [nz[min(len(nz) - 1, int(len(nz) * q))] for q in (0.25, 0.5, 0.75)]


def streaks(days: list[Day]) -> tuple[int, int]:
    """(current, longest) runs of days with at least one contribution."""
    longest = run = 0
    for d in days:
        run = run + 1 if d.count else 0
        longest = max(longest, run)
    tail = days[:-1] if days and not days[-1].count else days  # today may still be empty
    current = 0
    for d in reversed(tail):
        if not d.count:
            break
        current += 1
    return current, longest


def tile(x: float, y: int, w: float, value: str, label: str, colour: str, delay: float) -> str:
    return (
        f'<g class="rise" style="animation-delay:{delay:.2f}s">'
        f'<rect x="{x:g}" y="{y}" width="{w:g}" height="76" rx="12" fill="{INK}" stroke="{LINE}"/>'
        f'<rect x="{x:g}" y="{y + 18}" width="3" height="40" rx="1.5" fill="{colour}"/>'
        f'<text x="{x + 22:g}" y="{y + 40}" class="big" fill="{colour}">{esc(value)}</text>'
        f'<text x="{x + 22:g}" y="{y + 60}" class="mono-s" fill="{FAINT}">{esc(label)}</text></g>'
    )


def render_tiles(s: Stats, y: int) -> str:
    days = [d for w in s.weeks for d in w]
    current, longest = streaks(days)
    items = [
        (f"{s.total:,}", "contributions · 12 mo", MINT),
        (f"{s.pull_requests}", "pull requests", CORAL),
        (f"{current}d", "current streak", AMBER),
        (f"{longest}d", "longest streak", VIOLET),
    ]
    w = (WIDTH - 80 - 3 * 16) / 4
    return "".join(tile(40 + i * (w + 16), y, w, v, lbl, c, 1.0 + i * 0.1) for i, (v, lbl, c) in enumerate(items))


def render_grid(weeks: list[list[Day]], y: int) -> str:
    step = CELL + GAP
    grid_w = len(weeks) * step - GAP
    left = (WIDTH - grid_w) / 2
    cuts = level_cuts([d for w in weeks for d in w])
    cells, months, seen = [], [], None
    for col, week in enumerate(weeks):
        delay = SWEEP_S * col / len(weeks)
        if week[0].day.month != seen and col < len(weeks) - 2:
            seen = week[0].day.month
            months.append(f'<text class="mono-xs" x="{left + col * step:g}" y="{y}">{week[0].day.strftime("%b").lower()}</text>')
        for d in week:
            lvl = sum(d.count >= t for t in cuts) if d.count else 0
            cls = "c lit" if lvl else "c"
            cells.append(
                f'<rect class="{cls}" x="{left + col * step:g}" y="{y + 12 + d.day.isoweekday() % 7 * step}" '
                f'width="{CELL}" height="{CELL}" rx="3" fill="{GRID_PALETTE[lvl]}" style="animation-delay:{delay:.2f}s"/>'
            )
    beam_y, beam_h = y + 6, 7 * step + 8
    beam = (
        f'<clipPath id="gridclip"><rect x="{left - 2:g}" y="{beam_y}" width="{grid_w + 4}" height="{beam_h}"/></clipPath>'
        f'<g clip-path="url(#gridclip)"><rect class="beam" x="{left - 60:g}" y="{beam_y}" width="60" '
        f'height="{beam_h}" fill="url(#beam)" style="--w:{grid_w}px"/></g>'
    )
    return f'<g class="rise" style="animation-delay:1.4s">{"".join(months)}{"".join(cells)}{beam}</g>'


def render_languages(langs: list[tuple[str, int]], y: int) -> str:
    total = sum(n for _, n in langs) or 1
    top = langs[:5] + ([("other", sum(n for _, n in langs[5:]))] if len(langs) > 5 else [])
    colours = list(LANG_COLOURS) + [FAINT]
    bar_w, x, segs, legend, lx = WIDTH - 80, 40.0, [], [], 40.0
    for i, (name, n) in enumerate(top):
        w = bar_w * n / total
        segs.append(
            f'<rect x="{x:g}" y="{y}" width="0" height="8" fill="{colours[i]}">'
            f'<animate attributeName="width" from="0" to="{max(w - 2, 1):g}" begin="{1.8 + i * 0.12:.2f}s" dur=".7s" fill="freeze"/></rect>'
        )
        label = f"{name} {100 * n / total:.0f}%"
        legend.append(f'<circle cx="{lx + 4:g}" cy="{y + 30}" r="4" fill="{colours[i]}"/>'
                      f'<text x="{lx + 14:g}" y="{y + 34}" class="mono-s" fill="#b9b3c7">{esc(label)}</text>')
        x += w
        lx += 24 + 7.2 * len(label)
    return (
        f'<g class="rise" style="animation-delay:1.7s"><clipPath id="barclip"><rect x="40" y="{y}" width="{bar_w}" height="8" rx="4"/></clipPath>'
        f'<rect x="40" y="{y}" width="{bar_w}" height="8" rx="4" fill="#221f2c"/>'
        f'<g clip-path="url(#barclip)">{"".join(segs)}</g>{"".join(legend)}</g>'
    )


def render_stats(s: Stats, y: int) -> tuple[str, int]:
    """Returns (svg, height)."""
    tiles = render_tiles(s, y)
    grid = render_grid(s.weeks, y + 112)
    langs_head = f'<text x="40" y="{y + 268}" class="mono-s" fill="{FAINT}">languages · {s.repos} repos active this year</text>'
    langs = render_languages(s.languages, y + 282)
    return tiles + grid + langs_head + langs, 330
