from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Static

from .loop import GauntletLoop
from .models import PieceStatus, RunStatus

STATUS_GLYPH = {
    PieceStatus.QUEUED: "·",
    PieceStatus.BUILDING: "▸",
    PieceStatus.CRITIQUING: "◎",
    PieceStatus.WON: "●",
    PieceStatus.LOST: "○",
}


class GauntletTUI(App[None]):
    """Live gauntlet board: pieces, candidate vs bar, picks not scores."""

    TITLE = "ORC Gauntlet"
    CSS = """
    Screen {
        background: #101216;
        color: #e8e4d9;
        layout: vertical;
    }

    #masthead {
        height: 5;
        padding: 0 2;
        background: #1a1d22;
        border-bottom: tall #c9a227;
    }

    #brand {
        color: #f4e4c1;
        text-style: bold;
    }

    #meta {
        color: #9a9487;
    }

    #goal {
        color: #f2eee4;
        text-style: bold;
    }

    #bar {
        color: #e4b84a;
    }

    #board {
        height: 1fr;
    }

    #pieces {
        width: 32;
        padding: 1 1;
        background: #14171c;
        border-right: solid #2a2e35;
    }

    #pair {
        width: 1fr;
    }

    #candidate, #reference {
        width: 1fr;
        padding: 1 2;
        height: 1fr;
    }

    #candidate {
        background: #12181a;
        border-right: solid #2a2e35;
    }

    #reference {
        background: #18140e;
    }

    .panel-title {
        color: #9a9487;
        text-style: bold;
        padding-bottom: 1;
    }

    #preview-candidate {
        color: #d5ead2;
    }

    #preview-reference {
        color: #f0ddb0;
    }

    #verdicts {
        height: 8;
        padding: 0 2 0 2;
        background: #0c0e11;
        border-top: solid #2a2e35;
        color: #c4beb3;
    }

    Footer {
        background: #1a1d22;
    }
    """

    BINDINGS = [
        Binding("space", "toggle_pause", "Pause"),
        Binding("s", "stop", "Stop"),
        Binding("n", "nudge", "Step"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, loop: GauntletLoop, interval: float = 0.55) -> None:
        super().__init__()
        self.loop = loop
        self.interval = interval

    def compose(self) -> ComposeResult:
        yield Static(id="masthead")
        with Horizontal(id="board"):
            yield Static(id="pieces")
            with Horizontal(id="pair"):
                with Vertical(id="candidate"):
                    yield Static("CANDIDATE", classes="panel-title")
                    yield Static(id="preview-candidate")
                with Vertical(id="reference"):
                    yield Static("BAR", classes="panel-title")
                    yield Static(id="preview-reference")
        yield Static(id="verdicts")
        yield Footer()

    def on_mount(self) -> None:
        self.loop.start()
        self.set_interval(self.interval, self._tick)
        self._render_all()

    def _tick(self) -> None:
        if self.loop.state.status == RunStatus.RUNNING:
            self.loop.step()
            self._render_all()

    def _render_all(self) -> None:
        state = self.loop.state
        round_label = f"R{state.round_no:02d}"
        status = state.status.value.upper()
        active = state.active_piece_id or "—"
        self.query_one("#masthead", Static).update(
            f"[b]ORC GAUNTLET[/b]   {round_label}  {status}  piece {active}\n"
            f"[b]{state.goal}[/b]\n"
            f"BAR  {state.bar.name}\n"
            f"critic is blind · picks not scores · you are the brake"
        )
        lines = ["PIECES"]
        for piece in state.pieces:
            mark = STATUS_GLYPH[piece.status]
            focus = "◂" if piece.id == state.active_piece_id else " "
            lines.append(
                f"{focus}{mark} {piece.title:<8} {piece.status.value:<10} "
                f"{piece.wins}W {piece.losses}L"
            )
        self.query_one("#pieces", Static).update("\n".join(lines))
        self.query_one("#preview-candidate", Static).update(
            state.candidate_preview or "(builder has not shipped a viewport yet)"
        )
        self.query_one("#preview-reference", Static).update(
            state.reference_preview or "(bar not loaded)"
        )
        verdict_lines = ["VERDICTS"]
        for verdict in reversed(state.verdicts[-5:]):
            pick = verdict.winner.upper()
            verdict_lines.append(
                f"r{verdict.round_no}  {verdict.piece_id:<6}  PICK {pick:<10}  {verdict.reason}"
            )
        if len(verdict_lines) == 1:
            verdict_lines.append("Waiting for the first blind pair.")
        self.query_one("#verdicts", Static).update("\n".join(verdict_lines))

    def action_toggle_pause(self) -> None:
        if self.loop.state.status == RunStatus.PAUSED:
            self.loop.resume()
        else:
            self.loop.pause()
        self._render_all()

    def action_stop(self) -> None:
        self.loop.stop()
        self._render_all()

    def action_nudge(self) -> None:
        if self.loop.state.status == RunStatus.PAUSED:
            self.loop.state.status = RunStatus.RUNNING
            self.loop.step()
            self.loop.state.status = RunStatus.PAUSED
            self._render_all()
