"""Section: a terminal that types commands and prints their output on a loop."""

from __future__ import annotations

from dataclasses import dataclass

from card.content import Command, Output, Span
from card.theme import DIM, FAINT, INK, LINE, MINT, MONO, TEXT, WIDTH, esc

CHAR_W = 9.0          # px per char at 15px; textLength pins every font to this grid
LINE_H = 25
PROMPT: list[Span] = [("~", MINT), (" $ ", FAINT)]
TYPE_S, PAUSE_S, ENTER_S, HOLD_S = 0.075, 0.7, 0.3, 4.5


@dataclass
class Line:
    spans: list[Span]
    reveal: list[tuple[float, int]]  # (time, visible chars)


def build_lines(script: list[Command | Output], t0: float) -> tuple[list[Line], list[tuple[float, int, int]], float]:
    """Turn the script into timed lines plus caret positions (time, row, col)."""
    lines: list[Line] = []
    caret: list[tuple[float, int, int]] = []
    t = t0
    for item in script + [Command("")]:
        row = len(lines)
        if isinstance(item, Command):
            p = sum(len(s) for s, _ in PROMPT)
            reveal = [(t, p)]
            caret.append((t, row, p))
            t += PAUSE_S
            for k in range(1, len(item.text) + 1):
                reveal.append((t, p + k))
                caret.append((t, row, p + k))
                t += TYPE_S
            lines.append(Line(PROMPT + [(item.text, TEXT)], reveal))
            t += ENTER_S
        else:
            n = sum(len(s) for s, _ in item.spans)
            lines.append(Line(item.spans, [(t, n)]))
            t += 0.08
    return lines, caret, t + HOLD_S


RESET_S = 0.35  # the screen clears this long before the loop restarts


def step_keyframes(name: str, track: list[tuple[float, str]], period: float, rest: str) -> str:
    """Stepwise CSS keyframes: `rest` at 0%, each (time, value) from its time on, `rest` again at
    the reset. Everything in the terminal runs on this one CSS clock: Safari neither resets SMIL
    tracks on repeat nor keeps them in sync with CSS animations."""
    pts = [(0.0, rest)] + [(100 * t / period, v) for t, v in track] + [(100 * (period - RESET_S) / period, rest)]
    clean: list[tuple[float, str]] = []
    for pct, v in sorted(pts, key=lambda p: p[0]):
        if clean and pct - clean[-1][0] < 0.005:
            clean[-1] = (clean[-1][0], v)   # same instant: the later value wins
        else:
            clean.append((pct, v))
    # Hold each value explicitly until just before the next stop and run the animation linear:
    # engines disagree on how step-end applies inside keyframes (WebKit shows values a step early).
    stops = []
    for k, (pct, v) in enumerate(clean):
        nxt = clean[k + 1][0] if k + 1 < len(clean) else 100.0
        stops.append(f"{pct:.3f}%, {max(pct, nxt - 0.002):.3f}% {{ {v} }}")
    return f"@keyframes {name} {{ {' '.join(stops)} 100% {{ {rest} }} }}"


def animated(cls: str, period: float) -> str:
    return f".{cls} {{ animation: {cls} {period:.2f}s linear infinite; }}"


def render_line(i: int, line: Line, x: int, y: int, period: float) -> tuple[str, str]:
    """One text row under a cover the colour of the terminal, which slides right one character at a
    time to reveal it and slides back at the reset. Only transforms are animated: WebKit does not
    clip at all when an animated clip rect is zero-wide. Returns (svg, css)."""
    total = sum(len(s) for s, _ in line.spans)
    spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in line.spans)
    # One x per character pins every glyph to the CHAR_W grid, so sliding the cover by
    # n * CHAR_W uncovers exactly n characters.
    xs = " ".join(f"{x + k * CHAR_W:g}" for k in range(total))
    track = [(t, f"transform: translateX({n * CHAR_W:g}px);") for t, n in line.reveal]
    svg = (
        f'<text x="{xs}" y="{y}" class="tt" xml:space="preserve">{spans}</text>'
        f'<rect class="tl{i}" x="{x - 1}" y="{y - 17}" width="{total * CHAR_W + 6:g}" height="{LINE_H}" fill="{INK}"/>'
    )
    return svg, step_keyframes(f"tl{i}", track, period, "transform: translateX(0px);") + animated(f"tl{i}", period)


def render_caret(caret: list[tuple[float, int, int]], x: int, y0: int, period: float) -> tuple[str, str]:
    """Block caret that follows the typing and blinks. Returns (svg, css)."""
    _, row0, col0 = caret[0]
    move = [(t, f"transform: translate({(col - col0) * CHAR_W:g}px, {(row - row0) * LINE_H}px);") for t, row, col in caret]
    svg = (
        f'<g class="cm"><rect class="caret" x="{x + col0 * CHAR_W:g}" y="{y0 - 14 + row0 * LINE_H}" '
        f'width="{CHAR_W:g}" height="18" fill="{MINT}" opacity=".85"/></g>'
    )
    return svg, step_keyframes("cm", move, period, "transform: translate(0px, 0px);") + animated("cm", period)


def render_terminal(script: list[Command | Output], y: int, t0: float) -> tuple[str, int, str]:
    """Terminal panel at vertical offset y. Returns (svg, height, css)."""
    lines, caret, period = build_lines(script, t0)
    height = 58 + len(lines) * LINE_H
    tx, ty = 64, y + 62
    rendered = [render_line(i, ln, tx, ty + i * LINE_H, period) for i, ln in enumerate(lines)]
    rows, css = "".join(r for r, _ in rendered), "".join(c for _, c in rendered)
    bar = (
        f'<rect x="40" y="{y}" width="{WIDTH - 80}" height="{height}" rx="12" fill="{INK}" stroke="{LINE}"/>'
        f'<path d="M40 {y + 30} H{WIDTH - 40}" stroke="{LINE}"/>'
        + "".join(f'<circle cx="{60 + 16 * k}" cy="{y + 15}" r="4.5" fill="{c}"/>'
                  for k, c in enumerate(("#ff5f57", "#febc2e", "#28c840")))
        + f'<text x="{WIDTH / 2}" y="{y + 19}" class="mono-s" fill="{DIM}" text-anchor="middle">felipe — zsh</text>'
    )
    caret_svg, caret_css = render_caret(caret, tx, ty, period)
    # Covers slide right past the end of their line; keep them inside the window (static clip).
    inner = (f'<clipPath id="termclip"><rect x="41" y="{y + 31}" width="{WIDTH - 82}" height="{height - 32}" rx="11"/></clipPath>')
    svg = (f'<g class="rise" style="animation-delay:.35s">{bar}{inner}'
           f'<g clip-path="url(#termclip)">{rows}{caret_svg}</g></g>')
    return svg, height, css + caret_css
