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


def discrete(values: list[tuple[float, float]], period: float) -> str:
    """SMIL attributes for a stepwise track that resets to its first value each loop.

    keyTimes are strictly increasing from 0 to 1: Safari mishandles duplicate key times or a
    discrete track that ends before 1, and then fails to reset the loop.
    """
    start = values[0][1]
    pts = [(0.0, start)] + [(t / period, v) for t, v in values] + [((period - 0.35) / period, start), (1.0, start)]
    clean: list[tuple[float, float]] = []
    for kt, v in sorted(pts, key=lambda p: p[0]):
        if clean and kt - clean[-1][0] < 1e-4:
            clean[-1] = (clean[-1][0], v)   # same instant: the later value wins
        else:
            clean.append((kt, v))
    kt = ";".join(f"{k:.4f}" for k, _ in clean)
    vs = ";".join(f"{v:g}" for _, v in clean)
    return f'dur="{period:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{vs}"'


def render_line(i: int, line: Line, x: int, y: int, period: float) -> tuple[str, str]:
    """One text row. Typed rows widen a SMIL clip per character; rows that appear at once
    (outputs, the idle prompt) toggle opacity with CSS instead, because Safari does not reset
    single-step SMIL tracks when the loop repeats. Returns (svg, css)."""
    total = sum(len(s) for s, _ in line.spans)
    spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in line.spans)
    text = (f'<text x="{x}" y="{y}" class="tt{{cls}}"{{clip}} textLength="{total * CHAR_W:g}" '
            f'lengthAdjust="spacing" xml:space="preserve">{spans}</text>')
    if len(line.reveal) == 1:
        return text.format(cls=f" tl{i}", clip=""), appear_css(f"tl{i}", line.reveal[0][0], period)
    track = [(0.0, 0.0)] + [(t, n * CHAR_W) for t, n in line.reveal]
    clip = (
        f'<clipPath id="tl{i}"><rect x="{x}" y="{y - 16}" width="0" height="{LINE_H}">'
        f'<animate attributeName="width" {discrete(track, period)}/></rect></clipPath>'
    )
    return clip + text.format(cls="", clip=f' clip-path="url(#tl{i})"'), ""


def appear_css(cls: str, at: float, period: float) -> str:
    """Looping CSS keyframes: hidden, visible from `at` until the loop reset, hidden again."""
    on = 100 * at / period
    off = 100 * (period - 0.35) / period
    return (
        f"@keyframes {cls} {{ 0%, {on - 0.01:.3f}% {{ opacity: 0; }} {on:.3f}%, {off - 0.01:.3f}% {{ opacity: 1; }} "
        f"{off:.3f}%, 100% {{ opacity: 0; }} }}"
        f".{cls} {{ opacity: 0; animation: {cls} {period:.2f}s linear infinite; }}"
    )


def render_caret(caret: list[tuple[float, int, int]], x: int, y0: int, period: float) -> str:
    """Block caret that follows the typing and blinks while idle."""
    xs = [(t, x + col * CHAR_W) for t, _, col in caret]
    ys = [(t, y0 - 14 + row * LINE_H) for t, row, _ in caret]
    return (
        f'<rect class="caret" x="{xs[0][1]:g}" y="{ys[0][1]}" width="{CHAR_W:g}" height="18" fill="{MINT}" opacity=".85">'
        f'<animate attributeName="x" {discrete([(0, xs[0][1])] + xs, period)}/>'
        f'<animate attributeName="y" {discrete([(0, ys[0][1])] + ys, period)}/></rect>'
    )


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
    svg = f'<g class="rise" style="animation-delay:.35s">{bar}{rows}{render_caret(caret, tx, ty, period)}</g>'
    return svg, height, css
