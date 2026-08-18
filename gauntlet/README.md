# Gauntlet Loop TUI (ORC)

Operator board for a [Gauntlet Loop](https://github.com/robonuggets/gauntlet-loop): named quality bar, independently judged pieces, builder vs **blind** critic, picks not scores. The TUI is the live status page. You are the brake.

## Run the demo

```bash
python3 -m venv .venv
.venv/bin/pip install -r gauntlet/requirements.txt
.venv/bin/python -m gauntlet demo
```

Keys: `space` pause · `n` step while paused · `s` stop · `q` quit.

Headless grind (no TUI):

```bash
.venv/bin/python -m gauntlet demo --headless-steps 40
```

Paste-ready prompt for another harness:

```bash
.venv/bin/python -m gauntlet prompt --goal "…" --bar "Named fetchable reference"
```

## What the board shows

- **Pieces** with builder/critic/win state
- **Candidate vs BAR** first-viewport sketches from inspectable HTML, not from builder reasoning
- **Verdicts** as `PICK CANDIDATE` / `PICK REFERENCE` / `PICK INVALID`

State is written to `workspace/gauntlet/demo/status.json` (builder notes are not).
