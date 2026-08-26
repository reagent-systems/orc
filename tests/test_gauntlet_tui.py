from __future__ import annotations

import asyncio

from gauntlet.demo import demo_state, staged_builder
from gauntlet.loop import GauntletLoop
from gauntlet.models import RunStatus
from gauntlet.tui import GauntletTUI


def test_tui_shows_named_bar_and_pause() -> None:
    async def scenario() -> None:
        loop = GauntletLoop(demo_state(), builder=staged_builder)
        app = GauntletTUI(loop, interval=10)
        async with app.run_test() as pilot:
            await pilot.pause()
            masthead = str(app.query_one("#masthead").render())
            assert "ORC GAUNTLET" in masthead
            assert "Northstar Run campaign" in masthead
            assert "Landing page for a running brand" in masthead
            assert "you are the brake" in masthead
            pieces = str(app.query_one("#pieces").render())
            assert "Hero" in pieces
            assert "CTA" in pieces
            reference = str(app.query_one("#preview-reference").render())
            assert "Run until the road ends" in reference
            await pilot.press("space")
            assert loop.state.status == RunStatus.PAUSED
            await pilot.press("s")
            assert loop.state.status == RunStatus.STOPPED

    asyncio.run(scenario())
