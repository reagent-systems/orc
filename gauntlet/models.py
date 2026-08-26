from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class PieceStatus(str, Enum):
    QUEUED = "queued"
    BUILDING = "building"
    CRITIQUING = "critiquing"
    WON = "won"
    LOST = "lost"


class RunStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    WON = "won"
    STOPPED = "stopped"


@dataclass
class QualityBar:
    """A named, fetchable, comparable reference. Vague bars are rejected."""

    name: str
    source: str
    medium: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Piece:
    id: str
    title: str
    required_signals: List[str]
    status: PieceStatus = PieceStatus.QUEUED
    best_artifact: str = ""
    challenger_artifact: str = ""
    last_gap: str = ""
    wins: int = 0
    losses: int = 0
    rounds: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Piece":
        payload = dict(data)
        payload["status"] = PieceStatus(payload["status"])
        return cls(**payload)


@dataclass
class Verdict:
    round_no: int
    piece_id: str
    winner: str  # candidate | reference | invalid
    reason: str
    evidence_ok: bool
    left_label: str
    right_label: str
    picked_side: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Verdict":
        return cls(**data)


@dataclass
class RunState:
    goal: str
    bar: QualityBar
    pieces: List[Piece]
    status: RunStatus = RunStatus.IDLE
    round_no: int = 0
    active_piece_id: Optional[str] = None
    verdicts: List[Verdict] = field(default_factory=list)
    candidate_preview: str = ""
    reference_preview: str = ""
    candidate_artifact: str = ""
    builder_notes: List[str] = field(default_factory=list)
    stop_requested: bool = False

    def piece(self, piece_id: str) -> Piece:
        for piece in self.pieces:
            if piece.id == piece_id:
                return piece
        raise KeyError(piece_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "bar": self.bar.to_dict(),
            "pieces": [piece.to_dict() for piece in self.pieces],
            "status": self.status.value,
            "round_no": self.round_no,
            "active_piece_id": self.active_piece_id,
            "verdicts": [verdict.to_dict() for verdict in self.verdicts],
            "candidate_preview": self.candidate_preview,
            "reference_preview": self.reference_preview,
            "candidate_artifact": self.candidate_artifact,
            "stop_requested": self.stop_requested,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunState":
        return cls(
            goal=data["goal"],
            bar=QualityBar(**data["bar"]),
            pieces=[Piece.from_dict(item) for item in data["pieces"]],
            status=RunStatus(data.get("status", "idle")),
            round_no=data.get("round_no", 0),
            active_piece_id=data.get("active_piece_id"),
            verdicts=[Verdict.from_dict(item) for item in data.get("verdicts", [])],
            candidate_preview=data.get("candidate_preview", ""),
            reference_preview=data.get("reference_preview", ""),
            candidate_artifact=data.get("candidate_artifact", ""),
            stop_requested=data.get("stop_requested", False),
        )
