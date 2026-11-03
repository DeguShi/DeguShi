"""Hand-written content: the terminal script and the research/building topics."""

from __future__ import annotations

from dataclasses import dataclass

from card.theme import AMBER, CORAL, DIM, FAINT, MINT, SOFT, TEXT

Span = tuple[str, str]  # (text, colour)


@dataclass(frozen=True)
class Command:
    text: str


@dataclass(frozen=True)
class Output:
    spans: list[Span]


TERMINAL: list[Command | Output] = [
    Command("whoami"),
    Output([("felipe azambuja", TEXT), ("  ·  computer science @ usp  ·  são carlos, br", DIM)]),
    Command("ls research/"),
    Output([("ULRMEEUD/  Slt-Att-Le-WM/", MINT)]),
    Command("cat research/*/ABOUT"),
    Output([("ULRMEEUD       ", MINT), ("risk matrices for epidemic events, learned from the open web", SOFT)]),
    Output([("Slt-Att-Le-WM  ", MINT), ("object-centric world models for embodied agents · aalto", SOFT)]),
    Command("ls building/"),
    Output([("what-manga/  organisiani/  habitacion/  ", CORAL), ("class/  ", DIM), (".stealth/", AMBER)]),
    Command("ls building/class/"),
    Output([("orquidea/  angelin-htr/  ai-notebooks/  computer-graphics/  …", DIM)]),
    Command("cat building/.stealth/README"),
    Output([("pehnaporta", AMBER), ("  ·  not yet. soon.", SOFT)]),
    Command("open degushi.github.io"),
    Output([("↳ ", FAINT), ("click to see more", MINT)]),
]

RESEARCH_TOPICS = ["World Models", "Object-Centric Learning", "LLM Agents", "Graph Neural Networks", "Epidemic Modeling"]
BUILDING_TOPICS = ["Products", "Web Apps", "Mobile Apps", "APIs & Backends", "Data Pipelines"]
