from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import RunState


class RunStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def status_path(self) -> Path:
        return self.root / "status.json"

    def save(self, state: RunState) -> None:
        payload = state.to_dict()
        # Builder notes never go on disk where the critic (or the TUI bar panel) can read them.
        self.status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        events = self.root / "verdicts.jsonl"
        if state.verdicts:
            last = state.verdicts[-1]
            with events.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(last.to_dict()) + "\n")

    def load(self) -> Optional[RunState]:
        if not self.status_path.exists():
            return None
        return RunState.from_dict(json.loads(self.status_path.read_text(encoding="utf-8")))
