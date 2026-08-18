from __future__ import annotations

import random
from typing import Callable, Optional, Sequence, Tuple

from .bar import evidence_ok
from .models import Piece, QualityBar, Verdict


BuilderFn = Callable[[Piece, str, str], Tuple[str, str]]
CriticFn = Callable[[Piece, QualityBar, str, str], Verdict]


def default_builder(piece: Piece, current_best: str, last_gap: str) -> Tuple[str, str]:
    """Inject the next missing inspectable signal. Notes stay private to the builder."""
    artifact = current_best or (
        "<!doctype html><html><body>\n<header></header>\n</body></html>\n"
    )
    injected = None
    for signal in piece.required_signals:
        if signal.lower() not in artifact.lower():
            artifact = _inject_signal(artifact, signal)
            injected = signal
            break
    return artifact, f"builder note: injected {injected} for {piece.id} gap={last_gap!r}"


def _inject_signal(artifact: str, signal: str) -> str:
    if signal.lower().startswith("data-"):
        block = f"<section {signal}></section>\n"
    elif "<h1" in signal:
        block = "<h1>Draft headline</h1>\n"
    elif signal.startswith("--") or ":" in signal or signal.startswith("@"):
        block = f"<style>{signal} {{}}</style>\n"
    else:
        block = f"<div>{signal}</div>\n"
    return artifact.replace("</body>", block + "</body>")


def signal_hits(signals: Sequence[str], blob: str) -> int:
    lowered = blob.lower()
    return sum(1 for signal in signals if signal.lower() in lowered)


def blind_critic(
    piece: Piece,
    bar: QualityBar,
    candidate: str,
    reference: str,
    rng: Optional[random.Random] = None,
) -> Verdict:
    """
    Judge unlabeled artifacts. Never receives builder notes.
    Returns a pick, not a score. Bad evidence throws the round out.
    """
    rng = rng or random.Random()
    if not evidence_ok(candidate, bar.medium) or not evidence_ok(reference, bar.medium):
        return Verdict(
            round_no=0,
            piece_id=piece.id,
            winner="invalid",
            reason="Evidence unusable; round discarded. Prior best stays.",
            evidence_ok=False,
            left_label="A",
            right_label="B",
            picked_side="",
        )

    labeled = [("candidate", candidate), ("reference", reference)]
    rng.shuffle(labeled)
    (left_id, left_blob), (right_id, right_blob) = labeled[0], labeled[1]
    left_hits = signal_hits(piece.required_signals, left_blob)
    right_hits = signal_hits(piece.required_signals, right_blob)

    if left_hits == right_hits:
        candidate_complete = signal_hits(piece.required_signals, candidate) == len(
            piece.required_signals
        )
        if candidate_complete:
            winner_id = "candidate"
            picked_side = "left" if left_id == "candidate" else "right"
            reason = f"{piece.title} matches every inspectable gate."
        else:
            winner_id = "reference"
            picked_side = "left" if left_id == "reference" else "right"
            missing = _missing(piece, candidate)
            reason = "Tie. Harsh pick stays with the bar."
            if missing:
                reason += f" Biggest gap: {missing[0]}."
    elif left_hits > right_hits:
        winner_id = left_id
        picked_side = "left"
        reason = _reason(piece, winner_id, candidate)
    else:
        winner_id = right_id
        picked_side = "right"
        reason = _reason(piece, winner_id, candidate)

    return Verdict(
        round_no=0,
        piece_id=piece.id,
        winner=winner_id,
        reason=reason,
        evidence_ok=True,
        left_label="A",
        right_label="B",
        picked_side=picked_side,
    )


def _missing(piece: Piece, candidate: str) -> list[str]:
    return [signal for signal in piece.required_signals if signal.lower() not in candidate.lower()]


def _reason(piece: Piece, winner_id: str, candidate: str) -> str:
    missing = _missing(piece, candidate)
    if winner_id == "candidate":
        return f"{piece.title} wins the blind pair."
    if missing:
        return f"{piece.title} loses. Biggest gap: {missing[0]}."
    return f"{piece.title} loses. Bar still reads cleaner in the first viewport."
