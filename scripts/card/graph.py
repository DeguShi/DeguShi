"""Section: research and building topics scattered in one net, signals crossing between them."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from card.theme import CORAL, DIM, INK, MINT, WIDTH, esc

NODE_H, CHAR_W, PAD = 26, 7.0, 30      # pill sized to its label
AREA_H = 270
MARGIN_X, GAP = 40, 22                 # min clearance between pills
SEED = 7                               # fixed so the layout is stable across daily rebuilds
LINKS_PER_RESEARCH = 2


@dataclass(frozen=True)
class Node:
    label: str
    kind: str  # "research" | "building"
    x: float   # centre
    y: float

    @property
    def w(self) -> float:
        return len(self.label) * CHAR_W + PAD

    @property
    def colour(self) -> str:
        return MINT if self.kind == "research" else CORAL


def overlaps(a: Node, b: Node) -> bool:
    return abs(a.x - b.x) < (a.w + b.w) / 2 + GAP and abs(a.y - b.y) < NODE_H + GAP


def try_place(labels: list[tuple[str, str]], top: float, rng: random.Random) -> list[Node] | None:
    """One rejection-sampled layout, or None if a node couldn't fit."""
    nodes: list[Node] = []
    for label, kind in labels:
        w = len(label) * CHAR_W + PAD
        for _ in range(400):
            n = Node(label, kind, rng.uniform(MARGIN_X + w / 2, WIDTH - MARGIN_X - w / 2),
                     rng.uniform(top + NODE_H / 2, top + AREA_H - NODE_H / 2))
            if not any(overlaps(n, m) for m in nodes):
                nodes.append(n)
                break
        else:
            return None
    return nodes


def spread(nodes: list[Node]) -> float:
    """Smallest centre-to-centre distance (y weighted up, the area is wide and short)."""
    return min(math.hypot(a.x - b.x, 2.2 * (a.y - b.y)) for i, a in enumerate(nodes) for b in nodes[i + 1:])


def mixing(nodes: list[Node]) -> float:
    """Share of nodes whose nearest neighbour is the other kind (1.0 = fully interleaved)."""
    near = lambda a: min((b for b in nodes if b is not a), key=lambda b: math.hypot(a.x - b.x, a.y - b.y))  # noqa: E731
    return sum(near(n).kind != n.kind for n in nodes) / len(nodes)


def blocked(nodes: list[Node], pairs: list[tuple[Node, Node]]) -> int:
    """Links whose straight path runs underneath some other pill."""
    hits = 0
    for a, b in pairs:
        pts = [(a.x + (b.x - a.x) * t / 20, a.y + (b.y - a.y) * t / 20) for t in range(1, 20)]
        hits += any(abs(px - n.x) < n.w / 2 + 4 and abs(py - n.y) < NODE_H / 2 + 4
                    for n in nodes if n is not a and n is not b for px, py in pts)
    return hits


def components(nodes: list[Node], pairs: list[tuple[Node, Node]]) -> int:
    """Number of connected pieces in the net (union-find)."""
    parent = {id(n): id(n) for n in nodes}
    def root(k: int) -> int:
        while parent[k] != k:
            k = parent[k]
        return k
    for a, b in pairs:
        parent[root(id(a))] = root(id(b))
    return len({root(id(n)) for n in nodes})


def fill(nodes: list[Node]) -> float:
    """How much of the vertical band the nodes actually use (0-1)."""
    ys = [n.y for n in nodes]
    return (max(ys) - min(ys)) / (AREA_H - NODE_H)


def score(nodes: list[Node]) -> float:
    pairs = links(nodes)
    return (spread(nodes) / 120 + 2.0 * mixing(nodes) + 1.5 * fill(nodes)
            - 0.6 * blocked(nodes, pairs) - 3.0 * (components(nodes, pairs) - 1))


def place(labels: list[tuple[str, str]], top: float, tries: int = 1500) -> list[Node]:
    """Best of many seeded layouts: spread out, interleaved, links not hidden under pills."""
    rng = random.Random(SEED)
    layouts = [lay for _ in range(tries) if (lay := try_place(labels, top, rng))]
    if not layouts:
        raise RuntimeError("could not place graph nodes; lower GAP or raise AREA_H")
    return max(layouts, key=score)


def interleave(research: list[str], building: list[str]) -> list[tuple[str, str]]:
    pairs = [(t, "research") for t in research] + [(t, "building") for t in building]
    random.Random(SEED).shuffle(pairs)
    return pairs


def links(nodes: list[Node]) -> list[tuple[Node, Node]]:
    """Each research node reaches its nearest building nodes; every building node ends up with two or more."""
    res = [n for n in nodes if n.kind == "research"]
    bld = [n for n in nodes if n.kind == "building"]
    dist = lambda a, b: math.hypot(a.x - b.x, a.y - b.y)  # noqa: E731
    out = {(r, b) for r in res for b in sorted(bld, key=lambda b: dist(r, b))[:LINKS_PER_RESEARCH]}
    for b in bld:  # top every building node up to two links
        for r in sorted(res, key=lambda r: dist(r, b)):
            if sum(pair[1] is b for pair in out) >= 2:
                break
            out.add((r, b))
    return sorted(out, key=lambda p: (p[0].label, p[1].label))


def curve(a: Node, b: Node, k: int) -> str:
    """Gentle arc between two nodes, bending alternately left/right."""
    mx, my = (a.x + b.x) / 2, (a.y + b.y) / 2
    dx, dy = b.x - a.x, b.y - a.y
    bend = (0.18 if k % 2 else -0.18)
    return f"M{a.x:.1f} {a.y:.1f} Q{mx - dy * bend:.1f} {my + dx * bend:.1f} {b.x:.1f} {b.y:.1f}"


def edge(a: Node, b: Node, k: int) -> str:
    """Path with its own mint->coral gradient running from the research end to the building end."""
    return (
        f'<linearGradient id="g{k}" gradientUnits="userSpaceOnUse" x1="{a.x:.1f}" y1="{a.y:.1f}" x2="{b.x:.1f}" y2="{b.y:.1f}">'
        f'<stop offset="0" stop-color="{MINT}"/><stop offset="1" stop-color="{CORAL}"/></linearGradient>'
        f'<path id="w{k}" d="{curve(a, b, k)}" class="weave" stroke="url(#g{k})"/>'
    )


def signal(pid: str, k: int) -> str:
    """Two dots per edge: mint heading out, coral heading back, staggered so the net never syncs up."""
    dur = 3.2 + (k * 0.37) % 1.6
    begin = (k * 0.83) % dur
    back = 'keyPoints="1;0" keyTimes="0;1" calcMode="linear"'
    fade = 'attributeName="opacity" values="0;1;1;0" keyTimes="0;.1;.9;1"'
    return (
        f'<circle r="2.6" fill="{MINT}" opacity="0"><animateMotion dur="{dur:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"><mpath href="#{pid}"/></animateMotion>'
        f'<animate {fade} dur="{dur:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"/></circle>'
        f'<circle r="2.6" fill="{CORAL}" opacity="0"><animateMotion dur="{dur:.2f}s" begin="{begin + dur / 2:.2f}s" repeatCount="indefinite" {back}><mpath href="#{pid}"/></animateMotion>'
        f'<animate {fade} dur="{dur:.2f}s" begin="{begin + dur / 2:.2f}s" repeatCount="indefinite"/></circle>'
    )


def pill(n: Node, delay: float) -> str:
    x, y = n.x - n.w / 2, n.y - NODE_H / 2
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{n.w:.1f}" height="{NODE_H}" rx="{NODE_H / 2}" fill="{INK}" stroke="{n.colour}" stroke-opacity=".45"/>'
        f'<circle cx="{x + 13:.1f}" cy="{n.y:.1f}" r="3.5" fill="none" stroke="{n.colour}" class="ping" style="animation-delay:{delay:.2f}s"/>'
        f'<circle cx="{x + 13:.1f}" cy="{n.y:.1f}" r="3.5" fill="{n.colour}"/>'
        f'<text x="{x + 23:.1f}" y="{n.y + 4:.1f}" class="node">{esc(n.label)}</text>'
    )


def legend(y: int) -> str:
    x = WIDTH - 40
    return (
        f'<g class="mono-s" fill="{DIM}"><circle cx="{x - 166}" cy="{y}" r="3.5" fill="{MINT}"/><text x="{x - 156}" y="{y + 4}">research</text>'
        f'<circle cx="{x - 72}" cy="{y}" r="3.5" fill="{CORAL}"/><text x="{x - 62}" y="{y + 4}">building</text></g>'
    )


def render_graph(research: list[str], building: list[str], y: int) -> tuple[str, int, str]:
    """Returns (svg, height, extra css)."""
    nodes = place(interleave(research, building), y + 26)
    pairs = links(nodes)
    edges = "".join(edge(a, b, k) for k, (a, b) in enumerate(pairs))
    dots = "".join(signal(f"w{k}", k) for k in range(len(pairs)))
    pills = "".join(pill(n, i * 0.45) for i, n in enumerate(nodes))
    svg = f'<g class="rise" style="animation-delay:.6s">{legend(y - 26)}{edges}{dots}{pills}</g>'
    css = (
        ".weave { fill: none; stroke-width: 1.3; opacity: .55; stroke-dasharray: 3 6; animation: flow 2s linear infinite; }"
        ".ping { transform-box: fill-box; transform-origin: center; animation: ping 3s ease-out infinite; }"
        "@keyframes ping { 0% { transform: scale(1); opacity: .9; } 100% { transform: scale(3.2); opacity: 0; } }"
        f".node {{ font: 600 12px -apple-system, \"Segoe UI\", Helvetica, Arial, sans-serif; fill: #d9d4cc; }}"
    )
    return svg, AREA_H + 26, css
