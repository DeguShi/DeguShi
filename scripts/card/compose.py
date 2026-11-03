"""Stack the sections into one SVG with a shared background, spine and stylesheet."""

from __future__ import annotations

from card.theme import AMBER, CORAL, DIM, FAINT, INK, INK_2, LINE, MINT, MONO, SANS, SOFT, TEXT, WIDTH

BASE_CSS = f"""
.name {{ font: 800 56px {SANS}; letter-spacing: -1.5px; }}
.sub {{ font: 14px {MONO}; fill: {DIM}; letter-spacing: .5px; }}
.sec {{ font: 600 14px {MONO}; fill: {SOFT}; }}
.tag {{ font: 700 11px {MONO}; letter-spacing: 3px; }}
.tt {{ font: 15px {MONO}; }}
.mono-s {{ font: 12px {MONO}; }}
.mono-xs {{ font: 11px {MONO}; fill: {FAINT}; }}
.chip {{ font: 600 13px {SANS}; fill: {SOFT}; }}
.big {{ font: 800 28px {SANS}; letter-spacing: -.5px; }}

.rise {{ opacity: 0; animation: rise .9s ease-out forwards; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
.caret {{ animation: blink 1.05s steps(1) infinite; }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}

@keyframes flow {{ to {{ stroke-dashoffset: -18; }} }}
.c {{ transform-box: fill-box; transform-origin: center; animation: pop 7s ease-out infinite; }}
.c.lit {{ animation-name: glow; }}
@keyframes pop {{ 0% {{ transform: scale(1); }} 3% {{ transform: scale(.7); }} 8%, 100% {{ transform: scale(1); }} }}
@keyframes glow {{ 0% {{ transform: scale(1); filter: brightness(1); }} 3% {{ transform: scale(1.35); filter: brightness(1.6); }} 12%, 100% {{ transform: scale(1); filter: brightness(1); }} }}
.beam {{ animation: sweep 7s linear infinite; }}
@keyframes sweep {{ from {{ transform: translateX(0); }} to {{ transform: translateX(var(--w)); }} }}
.spine {{ stroke-dasharray: 2 6; animation: flow 1.6s linear infinite reverse; }}
"""


def defs(css: str, height: int) -> str:
    return f"""<defs>
<linearGradient id="bg" x1="0" y1="0" x2=".6" y2="1"><stop offset="0" stop-color="{INK}"/><stop offset="1" stop-color="{INK_2}"/></linearGradient>
<linearGradient id="name" x1="0" x2="1"><stop offset="0" stop-color="{MINT}"/><stop offset=".5" stop-color="{TEXT}"/><stop offset="1" stop-color="{CORAL}"/></linearGradient>
<linearGradient id="vline" gradientUnits="userSpaceOnUse" x1="0" y1="180" x2="0" y2="{height}"><stop offset="0" stop-color="{MINT}"/><stop offset="1" stop-color="{CORAL}"/></linearGradient>
<linearGradient id="beam" x1="0" x2="1"><stop offset="0" stop-color="{MINT}" stop-opacity="0"/><stop offset=".85" stop-color="{MINT}" stop-opacity=".18"/><stop offset="1" stop-color="{MINT}" stop-opacity=".9"/></linearGradient>
<radialGradient id="gm" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{MINT}" stop-opacity=".10"/><stop offset="1" stop-color="{MINT}" stop-opacity="0"/></radialGradient>
<radialGradient id="gc" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{CORAL}" stop-opacity=".10"/><stop offset="1" stop-color="{CORAL}" stop-opacity="0"/></radialGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".9" fill="{LINE}"/></pattern>
<style>{BASE_CSS}{css}</style>
</defs>"""


def backdrop(height: int) -> str:
    return (
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{height - 1}" rx="20" fill="url(#bg)" stroke="{LINE}"/>'
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{height - 1}" rx="20" fill="url(#dots)" opacity=".7"/>'
        f'<ellipse cx="180" cy="{height * .45:g}" rx="320" ry="420" fill="url(#gm)"/>'
        f'<ellipse cx="{WIDTH - 180}" cy="{height * .55:g}" rx="320" ry="420" fill="url(#gc)"/>'
    )


def header() -> str:
    return (
        f'<g class="rise"><text x="{WIDTH / 2}" y="98" class="name" text-anchor="middle" fill="url(#name)">Felipe Azambuja</text></g>'
        f'<g class="rise" style="animation-delay:.2s"><text x="{WIDTH / 2}" y="134" class="sub" text-anchor="middle">'
        f'University of São Paulo · São Carlos, BR</text></g>'
    )


def spine(marks: list[int], bottom: int) -> str:
    """Thin vertical thread on the left edge tying the sections together."""
    top = marks[0] - 5
    dots = "".join(f'<circle cx="22" cy="{m - 5}" r="3.5" fill="{INK}" stroke="url(#vline)" stroke-width="1.5"/>' for m in marks)
    return (
        f'<path id="spine" d="M22 {top} V{bottom}" class="spine" stroke="url(#vline)" stroke-width="1.2" fill="none"/>'
        f'<circle r="2.6" fill="#ffffff"><animateMotion dur="9s" repeatCount="indefinite"><mpath href="#spine"/></animateMotion></circle>'
        f'{dots}<circle cx="22" cy="{bottom}" r="3.5" fill="{AMBER}"/>'
    )


def compose(body: str, height: int, css: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" '
        f'role="img" aria-label="Felipe Azambuja, University of São Paulo: research and building, projects and GitHub activity">'
        f"{defs(css, height)}{backdrop(height)}{body}</svg>"
    )
