from __future__ import annotations

import argparse
import sys

from .demo import BAR, GOAL, demo_state, demo_store, staged_builder
from .loop import GauntletLoop, validate_bar
from .models import QualityBar
from .tui import GauntletTUI


PROMPT_TEMPLATE = """Build {goal}

The bar is {bar}. Get the real thing first and compare against it directly, not against a description of it.

Break this into the smallest pieces that can be improved and judged on their own. For each piece, fan out a builder and a separate critic with fresh context. The critic inspects the actual output, puts it next to the bar blind with the labels stripped, says which one is better, and names the single biggest remaining gap. Then it goes back to the builder.

The critic should be a harsh critic. Praise is not useful. If ours does not win, it keeps going.

Keep looping until the critic picks ours. Run the builders and critics as parallel subagents. Do not stop before that.

Keep a live progress page updating as the work evolves so I can watch it.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gauntlet", description="ORC Gauntlet loop TUI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="Run the Northstar fixture against a named on-disk bar")
    demo.add_argument("--interval", type=float, default=0.55)
    demo.add_argument("--headless-steps", type=int, default=0, help="Run N loop steps without the TUI")

    prompt = sub.add_parser("prompt", help="Print a paste-ready gauntlet prompt")
    prompt.add_argument("--goal", default=GOAL)
    prompt.add_argument("--bar", default=BAR.name)

    args = parser.parse_args(argv)

    if args.cmd == "prompt":
        bar = QualityBar(name=args.bar, source=BAR.source, medium="html")
        error = validate_bar(bar)
        if error:
            print(error, file=sys.stderr)
            return 2
        sys.stdout.write(PROMPT_TEMPLATE.format(goal=args.goal, bar=args.bar).strip() + "\n")
        return 0

    store = demo_store()
    loop = GauntletLoop(demo_state(), store=store, builder=staged_builder)
    if args.headless_steps:
        loop.start()
        for _ in range(args.headless_steps):
            if loop.state.status.value in {"won", "stopped"}:
                break
            loop.step()
        print(store.status_path)
        print(loop.state.status.value, "rounds", loop.state.round_no)
        return 0

    app = GauntletTUI(loop, interval=args.interval)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
