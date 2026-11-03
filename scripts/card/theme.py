"""Shared palette, fonts and small SVG helpers."""

from __future__ import annotations

from html import escape

WIDTH = 960
MINT = "#2DD4BF"
CORAL = "#FF7A59"
AMBER = "#F5B83D"
VIOLET = "#A78BFA"
SKY = "#60A5FA"
INK = "#14121c"
INK_2 = "#1b1826"
LINE = "#2a2636"
TEXT = "#f2efe9"
SOFT = "#d9d4cc"
DIM = "#8a849c"
FAINT = "#6f6982"

SANS = '-apple-system, "Segoe UI", Helvetica, Arial, sans-serif'
MONO = 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace'


def esc(text: str) -> str:
    """Escape text for SVG content and attributes."""
    return escape(text, quote=True)


def section_header(y: int, index: str, title: str) -> str:
    """Mono comment-style divider that labels a section, e.g. `── 02 / graph ─────`."""
    return (
        f'<g class="rise" style="animation-delay:{0.15 + int(index) * 0.2:.2f}s">'
        f'<text x="40" y="{y}" class="sec"><tspan fill="{MINT}">{esc(index)}</tspan>'
        f'<tspan fill="{FAINT}"> / </tspan>{esc(title)}</text>'
        f'<line x1="{56 + 8.4 * (len(index) + len(title) + 3):g}" y1="{y - 4}" x2="{WIDTH - 40}" y2="{y - 4}" '
        f'stroke="#3a3549" stroke-dasharray="2 5"/></g>'
    )
