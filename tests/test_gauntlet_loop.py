from __future__ import annotations

from pathlib import Path

import pytest

from gauntlet.bar import evidence_ok, extract_preview, validate_bar
from gauntlet.demo import BAR, demo_state, staged_builder
from gauntlet.loop import GauntletLoop
from gauntlet.models import Piece, PieceStatus, QualityBar, RunState, RunStatus
from gauntlet.pairs import blind_critic, default_builder, signal_hits
from gauntlet.store import RunStore


def test_vague_bar_rejected(tmp_path: Path) -> None:
    bar = QualityBar(name="premium modern site", source=str(tmp_path / "missing.html"), medium="html")
    assert validate_bar(bar)


def test_named_on_disk_bar_accepted() -> None:
    assert validate_bar(BAR) is None


def test_critic_picks_not_scores() -> None:
    piece = Piece("hero", "Hero", ["<h1", "full-bleed"])
    candidate = "<html><body><h1>Hi</h1></body></html>"
    reference = "<html><body><header class='full-bleed'><h1>Bar</h1></header></body></html>"
    verdict = blind_critic(piece, BAR, candidate, reference)
    assert verdict.winner in {"candidate", "reference"}
    assert "10" not in verdict.reason
    assert "score" not in verdict.reason.lower()


def test_critic_does_not_see_builder_notes() -> None:
    piece = Piece("cta", "CTA", ["Shop the kit"])
    artifact, note = default_builder(piece, "<html><body></body></html>", "need louder CTA")
    assert "builder note" in note
    verdict = blind_critic(piece, BAR, artifact, "<html><body>Shop the kit</body></html>")
    assert "builder note" not in verdict.reason
    assert "tried" not in verdict.reason.lower()


def test_bad_evidence_is_invalid() -> None:
    piece = Piece("hero", "Hero", ["<h1"])
    verdict = blind_critic(piece, BAR, "", "<html><body>ok</body></html>")
    assert verdict.winner == "invalid"
    assert verdict.evidence_ok is False


def test_ratchet_keeps_best_on_invalid(tmp_path: Path) -> None:
    state = demo_state()
    loop = GauntletLoop(state, store=RunStore(tmp_path), builder=staged_builder)
    loop.start()
    loop.step()
    piece = loop.state.pieces[0]
    piece.best_artifact = "<html><body><h1>kept</h1></body></html>"
    piece.challenger_artifact = ""
    piece.status = PieceStatus.CRITIQUING
    loop._critique(piece)
    assert piece.best_artifact.startswith("<html><body><h1>kept")


def test_demo_loop_can_win_all_pieces(tmp_path: Path) -> None:
    loop = GauntletLoop(demo_state(), store=RunStore(tmp_path), builder=staged_builder)
    loop.start()
    for _ in range(80):
        loop.step()
        if loop.state.status == RunStatus.WON:
            break
    assert loop.state.status == RunStatus.WON
    assert all(piece.status == PieceStatus.WON for piece in loop.state.pieces)
    assert loop.state.round_no > 0


def test_user_stop_is_the_brake(tmp_path: Path) -> None:
    loop = GauntletLoop(demo_state(), store=RunStore(tmp_path), builder=staged_builder)
    loop.start()
    loop.step()
    loop.stop()
    assert loop.step() is None
    assert loop.state.status == RunStatus.STOPPED


def test_preview_sketches_first_viewport() -> None:
    html = Path(BAR.source).read_text(encoding="utf-8")
    preview = extract_preview(html)
    assert "Run until the road ends" in preview
    assert "Shop the kit" in preview


def test_evidence_gate_requires_html_body() -> None:
    assert evidence_ok("<html><body>x</body></html>", "html")
    assert not evidence_ok("<html></html>", "html")
