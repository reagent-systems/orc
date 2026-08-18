from __future__ import annotations

from pathlib import Path

from .bar import workspace_root
from .models import Piece, QualityBar, RunState
from .store import RunStore

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

GOAL = "Landing page for a running brand: athletic, dark, green, first viewport unmistakable."

BAR = QualityBar(
    name="Northstar Run campaign — desktop capture",
    source=str(FIXTURE_DIR / "northstar-run-campaign.html"),
    medium="html",
    notes="Named fixture. Critic opens this file, not a description of it.",
)

_PIECE_SPECS = (
    ("hero", "Hero", ["data-piece=\"hero\"", "<h1", "full-bleed"]),
    ("type", "Type", ["Newsreader", "letter-spacing"]),
    ("colour", "Colour", ["--volt", "--ink", "background:#0b1210"]),
    ("cta", "CTA", ["data-cta=\"primary\"", "Shop the kit"]),
    ("motion", "Motion", ["@keyframes stride", "animation:"]),
)

# Staged candidate HTML so the TUI preview actually fills in, one gap at a time.
_STAGE = {
    "hero": [
        '<header data-piece="hero"><p>Draft header</p></header>',
        '<header data-piece="hero"><h1>Go farther.</h1></header>',
        '<header data-piece="hero" class="full-bleed"><h1>Go farther.</h1><p class="lede">A course, not a crowd.</p></header>',
    ],
    "type": [
        "<style>body{font-family: Newsreader, serif}</style>",
        "<style>body{font-family: Newsreader, serif; letter-spacing: 0.04em}</style>",
    ],
    "colour": [
        "<style>:root{--ink:#0b1210}</style>",
        "<style>:root{--ink:#0b1210;--volt:#b6ff3b}</style>",
        "<style>:root{--ink:#0b1210;--volt:#b6ff3b}body{background:#0b1210}</style>",
    ],
    "cta": [
        "<nav><a href='#kit'>See kit</a></nav>",
        '<nav><a data-cta="primary" href="#kit">Shop the kit</a></nav>',
    ],
    "motion": [
        "<style>@keyframes stride { from { opacity: .7 } to { opacity: 1 } }</style>",
        "<style>@keyframes stride { from { opacity: .7 } to { opacity: 1 } } header { animation: stride 1.2s ease-out; }</style>",
    ],
}


def new_pieces() -> list[Piece]:
    return [
        Piece(piece_id, title, list(signals))
        for piece_id, title, signals in _PIECE_SPECS
    ]


def demo_state() -> RunState:
    return RunState(goal=GOAL, bar=BAR, pieces=new_pieces())


def demo_store() -> RunStore:
    root = workspace_root() / "gauntlet" / "demo"
    return RunStore(root)


def staged_builder(piece: Piece, current_best: str, last_gap: str) -> tuple[str, str]:
    """Private builder. Notes must never be handed to the critic."""
    stages = _STAGE[piece.id]
    body = current_best if current_best.strip() else _empty_page()
    applied = None
    for fragment in stages:
        if fragment not in body:
            body = body.replace("</body>", fragment + "\n</body>")
            applied = fragment[:48]
            break
    note = f"builder closed {piece.id} via {applied or 'noop'} given gap {last_gap!r}"
    return body, note


def _empty_page() -> str:
    return (
        "<!doctype html><html><body>\n"
        "<main><p>Placeholder page</p></main>\n"
        "</body></html>\n"
    )
