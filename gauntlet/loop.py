from __future__ import annotations

import random
from typing import Optional

from .bar import extract_preview, load_text, validate_bar
from .models import Piece, PieceStatus, QualityBar, RunState, RunStatus, Verdict
from .pairs import BuilderFn, CriticFn, blind_critic, default_builder, signal_hits
from .store import RunStore


class GauntletLoop:
    """
    One step = one builder pass or one blind critique.

    Exit is winning every piece, or the operator stopping the run.
    There is no round cap in the engine.
    """

    def __init__(
        self,
        state: RunState,
        store: Optional[RunStore] = None,
        builder: Optional[BuilderFn] = None,
        critic: Optional[CriticFn] = None,
        rng: Optional[random.Random] = None,
    ):
        error = validate_bar(state.bar)
        if error:
            raise ValueError(error)
        self.state = state
        self.store = store
        self.builder = builder or default_builder
        self.critic = critic or (
            lambda piece, bar, candidate, reference: blind_critic(
                piece, bar, candidate, reference, rng=self.rng
            )
        )
        self.rng = rng or random.Random()
        self.reference_blob = load_text(state.bar.source)
        self.state.reference_preview = extract_preview(self.reference_blob)

    def start(self) -> None:
        if self.state.status == RunStatus.STOPPED:
            return
        self.state.status = RunStatus.RUNNING
        self.state.stop_requested = False
        self._persist()

    def pause(self) -> None:
        if self.state.status == RunStatus.RUNNING:
            self.state.status = RunStatus.PAUSED
            self._persist()

    def resume(self) -> None:
        if self.state.status == RunStatus.PAUSED:
            self.state.status = RunStatus.RUNNING
            self._persist()

    def stop(self) -> None:
        self.state.stop_requested = True
        self.state.status = RunStatus.STOPPED
        self._persist()

    def step(self) -> Optional[Verdict]:
        if self.state.status == RunStatus.PAUSED:
            return None
        if self.state.stop_requested or self.state.status == RunStatus.STOPPED:
            self.state.status = RunStatus.STOPPED
            return None
        if all(piece.status == PieceStatus.WON for piece in self.state.pieces):
            self.state.status = RunStatus.WON
            self.state.active_piece_id = None
            self._persist()
            return None

        self.state.status = RunStatus.RUNNING
        piece = self._select_piece()
        self.state.active_piece_id = piece.id

        if piece.status in {PieceStatus.QUEUED, PieceStatus.LOST, PieceStatus.BUILDING}:
            return self._build(piece)
        if piece.status == PieceStatus.CRITIQUING:
            return self._critique(piece)
        return None

    def _select_piece(self) -> Piece:
        for piece in self.state.pieces:
            if piece.status == PieceStatus.CRITIQUING:
                return piece
        for piece in self.state.pieces:
            if piece.status != PieceStatus.WON:
                return piece
        return self.state.pieces[0]

    def _build(self, piece: Piece) -> Optional[Verdict]:
        piece.status = PieceStatus.BUILDING
        artifact, note = self.builder(piece, piece.best_artifact, piece.last_gap)
        piece.challenger_artifact = artifact
        self.state.builder_notes.append(note)
        self.state.candidate_preview = extract_preview(artifact)
        piece.status = PieceStatus.CRITIQUING
        self._persist()
        return None

    def _critique(self, piece: Piece) -> Verdict:
        self.state.round_no += 1
        piece.rounds += 1
        verdict = self.critic(
            piece, self.state.bar, piece.challenger_artifact, self.reference_blob
        )
        verdict.round_no = self.state.round_no
        verdict.piece_id = piece.id

        if not verdict.evidence_ok or verdict.winner == "invalid":
            piece.status = PieceStatus.LOST
            piece.last_gap = verdict.reason
        elif verdict.winner == "candidate":
            piece.best_artifact = piece.challenger_artifact
            piece.status = PieceStatus.WON
            piece.wins += 1
            piece.last_gap = ""
            self.state.candidate_preview = extract_preview(piece.best_artifact)
        else:
            piece.losses += 1
            piece.last_gap = verdict.reason
            piece.status = PieceStatus.LOST
            if (
                piece.challenger_artifact.strip()
                and signal_hits(piece.required_signals, piece.challenger_artifact)
                >= signal_hits(piece.required_signals, piece.best_artifact)
            ):
                piece.best_artifact = piece.challenger_artifact
                self.state.candidate_preview = extract_preview(piece.best_artifact)

        self.state.verdicts.append(verdict)
        self._persist()
        return verdict

    def _persist(self) -> None:
        if self.store:
            self.store.save(self.state)
