# Gauntlet Loop TUI (ORC)

Operator board for a [Gauntlet Loop](https://github.com/robonuggets/gauntlet-loop): named quality bar, independently judged pieces, builder vs **blind** critic, picks not scores. The TUI is the live status page. You are the brake.

## Run the demo

```bash
./scripts/cloud-agent-install.sh
.venv/bin/python -m gauntlet demo
# Cloud Agents keep a durable venv at ~/.orc-venv
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
