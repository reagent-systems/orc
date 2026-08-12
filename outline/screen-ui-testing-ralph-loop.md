# Real Screen & UI Testing as a Ralph Loop

## Goal

Add **real screen/UI testing** to ORC: open a live UI (browser or desktop surface), interact with it, capture screenshots/video, assert what humans would see, and **loop until acceptance criteria pass or a hard stop is hit**.

This is not unit/API testing. The current `TestAgent` covers pytest/unittest/jest/mocha. Screen/UI work needs a separate specialist that can drive a real viewport and judge visual + interactive outcomes.

## What a Ralph Loop Means Here

A **Ralph loop** is a persistent iterate-until-done cycle:

```
seed acceptance criteria
        │
        ▼
┌──────────────────────┐
│  OBSERVE (screen)    │  screenshot / DOM / console / network
│  ACT (interact)      │  click, type, navigate, resize
│  EVALUATE (judge)    │  pass / fail / unknown vs criteria
│  FIX or RETRY        │  emit repair tasks or re-run steps
└──────────┬───────────┘
           │
     criteria met? ──yes──► COMPLETE (artifacts + report)
           │
           no
           │
     budget exhausted? ──yes──► FAIL (last evidence + blockers)
           │
           no
           └──► next iteration
```

Key properties:

- **Same goal every iteration** — original acceptance criteria never drift
- **Evidence-backed** — every judgment attaches screenshots, logs, or recordings
- **Hard stops** — max iterations, wall-clock budget, repeated identical failure
- **Repair is explicit** — failed UI assertions become FileAgent/TerminalAgent tasks, then the loop re-tests

This maps cleanly onto ORC’s existing `monitor_workspace` loop, with one critical difference: a single UI verification goal stays **active across many observe→act→evaluate cycles** instead of completing after one LLM pass.

---

## Gap Analysis (Today)

| Capability | Current state |
|---|---|
| Unit / suite execution | `TestAgent` via pytest/unittest/jest/mocha |
| Lint / coverage | `TestAgent` |
| Browser automation | Missing |
| Screenshot / visual assert | Missing |
| Screen recording review | Missing |
| Persistent retest-until-green | Missing (tasks complete after one executor pass) |
| Monitoring Web UI | Listed as future work in README; no app to test yet |

Implication: either (a) build a minimal monitoring UI *and* the screen tester together, or (b) implement the screen tester against an external `base_url` / fixture app first. Prefer **(b) first** so the Ralph loop is real before ORC has its own UI.

---

## Proposed Agent: `ScreenUIAgent`

### Placement

- New package: `screen-ui-agent/` (Priority 2.5 — next to `TestAgent`, not inside it)
- Capabilities: `["ui_testing", "browser_automation", "visual_verification", "screen_recording"]`
- Claims tasks with those requirements or type `ui_verification` / `ralph_ui_loop`

Keep `TestAgent` for code-level QA. `ScreenUIAgent` owns viewport reality.

### Tools (executor surface)

| Operation | Purpose |
|---|---|
| `launch_browser` | Start headed/headless Chromium (Playwright) against `base_url` |
| `navigate` | Go to path / URL |
| `interact` | Click, fill, select, hover, keyboard, scroll |
| `wait_for` | Selector, network idle, text, URL |
| `screenshot` | Full page / element / viewport → `workspace/results/ui/<run_id>/` |
| `record_start` / `record_stop` | Optional video of the session |
| `read_console` / `read_network` | Capture JS errors and failed requests |
| `assert_visible` | Selector + text / accessibility name present |
| `assert_visual` | Diff screenshot vs baseline (pixel or LLM vision judge) |
| `resize_viewport` | Desktop / tablet / mobile presets |
| `close_browser` | Teardown |

Implementation note: Playwright is the default driver. Prefer one browser context per Ralph run so cookies/state are intentional.

### Three-LLM roles (Ralph-specific)

- **Executor** — drives Playwright tools; never invents pass/fail without evidence
- **Evaluator** — fitness for claiming UI tasks; also scores “is this a screen task vs unit test?”
- **Metacognition** — loop governor: should we proceed, step back, request a fix task, or stop?

Metacognition owns Ralph control:

```
PROCEED_NEXT_STEP | REQUEST_FIX | COMPLETE | ABORT
```

---

## Task Schema for a Ralph UI Run

```json
{
  "id": "ui-ralph-<uuid>",
  "type": "ralph_ui_loop",
  "description": "Verify monitoring dashboard: agents list loads and task folders render",
  "requirements": ["ui_testing", "browser_automation", "visual_verification"],
  "priority": "high",
  "context": {
    "original_goal": "Monitoring UI is usable on desktop and mobile widths",
    "base_url": "http://127.0.0.1:5173",
    "viewports": ["1280x720", "390x844"],
    "max_iterations": 8,
    "wall_clock_seconds": 1200,
    "acceptance": [
      {
        "id": "A1",
        "assert": "visible",
        "selector": "[data-testid='agent-list']",
        "description": "Agent list is visible on /"
      },
      {
        "id": "A2",
        "assert": "text",
        "selector": "h1",
        "equals": "ORC Monitor",
        "description": "Brand/title is hero-level on first viewport"
      },
      {
        "id": "A3",
        "assert": "no_console_errors",
        "description": "No uncaught JS errors during smoke path"
      },
      {
        "id": "A4",
        "assert": "screenshot_baseline",
        "path": "/",
        "viewport": "1280x720",
        "tolerance": 0.02
      }
    ],
    "smoke_path": [
      {"action": "navigate", "path": "/"},
      {"action": "wait_for", "selector": "[data-testid='agent-list']"},
      {"action": "screenshot", "name": "home-desktop"}
    ]
  },
  "max_retries": 1
}
```

Rules:

- `acceptance[]` is the **immutable contract** for the loop
- `smoke_path` is the default script; the agent may insert waits/retries but must not weaken assertions
- Results land in `workspace/results/ui/<task_id>/iteration_N/`

---

## Ralph Loop Inside ORC

### State machine (per claimed task)

```
CLAIMED
  → BOOTSTRAP (ensure app up; else spawn TerminalAgent start task + wait)
  → ITERATE
       OBSERVE → ACT → EVALUATE
         ├─ all acceptance PASS → COMPLETE
         ├─ FAIL + fixable → EMIT_FIX_TASKS → WAIT_DEPS → ITERATE
         ├─ FAIL + not fixable / identical 3x → ABORT
         └─ budget hit → ABORT
  → ARTIFACTS (report.json, screenshots, optional video)
  → MOVE task to completed/ or failed/
```

### Loop body (pseudocode)

```python
async def run_ralph_ui_loop(self, task):
    ctx = task["context"]
    criteria = ctx["acceptance"]
    run_dir = results_dir(task["id"])
    history = []  # fingerprints of failures to detect stuck loops

    await self.ensure_target_available(ctx["base_url"])
    browser = await self.tools.launch_browser(base_url=ctx["base_url"])

    try:
        for i in range(1, ctx["max_iterations"] + 1):
            if wall_clock_exceeded(ctx):
                return self.abort(task, "wall_clock", history)

            iter_dir = run_dir / f"iteration_{i}"
            evidence = await self.execute_smoke_path(browser, ctx, iter_dir)
            verdict = await self.judge_acceptance(criteria, evidence)

            history.append(verdict.fingerprint())
            self.write_iteration_report(iter_dir, verdict, evidence)

            if verdict.all_passed:
                return self.complete(task, verdict, history)

            if stuck(history, repeat=3):
                return self.abort(task, "identical_failure", history)

            decision = await self.metacognition_decide(task, verdict)
            if decision == "ABORT":
                return self.abort(task, "metacognition", history)
            if decision == "REQUEST_FIX":
                fix_ids = self.emit_fix_tasks(task, verdict)
                await self.wait_for_dependencies(fix_ids)
            # else PROCEED_NEXT_STEP → retry with same criteria
    finally:
        await browser.close()
```

### Emitting fix tasks

When evaluation fails, do **not** silently mutate the UI app from `ScreenUIAgent`. Emit focused downstream tasks:

```json
{
  "type": "file_operations",
  "description": "Fix missing data-testid=\"agent-list\" on monitoring dashboard home",
  "requirements": ["file_operations", "code_analysis"],
  "dependencies": [],
  "context": {
    "original_goal": "...",
    "parent_ralph_task": "ui-ralph-...",
    "failure_id": "A1",
    "evidence_path": "workspace/results/ui/.../iteration_3/home-desktop.png"
  }
}
```

Parent Ralph task stays in `active/` (or a new `tasks/waiting/` if we add it) with `dependencies: [fix_task_ids]` until fixes complete, then resumes iteration.

Optional: add `tasks/waiting/` to the workspace layout so long Ralph runs do not look stuck in `active/`.

---

## Judgment Model

Prefer **deterministic asserts first**, vision second:

1. Playwright locators / text / URL / console / network → hard pass/fail
2. Screenshot baseline diff (pixelmatch / Playwright `toHaveScreenshot`) → hard pass/fail with tolerance
3. LLM vision on screenshot **only** for criteria marked `"assert": "visual_llm"` (layout, brand dominance, “first viewport clutter”) — always store the image + model rationale

Never mark COMPLETE without writing `report.json`:

```json
{
  "task_id": "...",
  "iterations": 4,
  "status": "passed",
  "acceptance": {
    "A1": {"status": "pass", "evidence": "..."},
    "A2": {"status": "pass", "evidence": "..."}
  },
  "artifacts": [".../final.png", ".../session.webm"]
}
```

---

## Bootstrap / Fixture Strategy

### Phase 0 — Fixture app (unblock the loop)

Ship a tiny static or Vite fixture under `screen-ui-agent/fixtures/sample-app/` with:

- One landing view + one interactive control
- Stable `data-testid` hooks
- Intentional broken mode via `?broken=1` for loop demos

Ralph loop CI path: start fixture → run ralph task → expect PASS (or PASS after injected FileAgent fix in integration demo).

### Phase 1 — ORC monitoring UI

When the monitoring Web UI is built, point the same Ralph harness at it. Acceptance criteria should mirror product rules (brand-first hero, no clutter in first viewport, desktop + mobile).

### Process ownership

- `TerminalAgent` (or ScreenUIAgent bootstrap) starts the app if health check fails
- Health check: HTTP GET `base_url` within timeout
- Never leave orphan browsers: always `close_browser` in `finally`

---

## Workspace Layout Additions

```
workspace/
├── tasks/
│   ├── pending/
│   ├── active/
│   ├── waiting/      # NEW (optional): Ralph parent waiting on fix deps
│   ├── completed/
│   └── failed/
├── results/
│   └── ui/
│       └── <task_id>/
│           ├── report.json
│           ├── iteration_1/
│           │   ├── home-desktop.png
│           │   └── verdict.json
│           └── session.webm
└── baselines/        # NEW: committed screenshot baselines
    └── ui/
        └── monitoring-home-1280x720.png
```

Baselines are git-tracked; updates require an explicit `update_baselines: true` context flag.

---

## Integration With Existing Agents

| Agent | Role in Ralph UI flow |
|---|---|
| TaskBreakdownAgent | Splits “ship + verify UI” into build, start, ralph_ui_loop |
| FileAgent | Applies code fixes from failed acceptance items |
| TerminalAgent | Installs Playwright browsers, starts/stops app servers |
| TestAgent | Remains unit/integration owner; may run after UI fixes |
| GitAgent | Commits baseline updates when explicitly tasked |
| ScreenUIAgent | Owns the Ralph screen loop |

Natural equilibrium: ScreenUIAgent threshold high for pure UI tasks (~8), low for “run pytest”.

---

## Implementation Plan

### Step 1 — Harness skeleton

- Create `screen-ui-agent/` mirroring `test-agent/` layout (`agent.py`, `run_autonomous.py`, `create_test_task.py`)
- Add Playwright dependency + install instructions in agent README
- Implement tool ops: launch, navigate, interact, screenshot, close
- Single-shot mode first (run smoke_path once, write report) to prove tooling

### Step 2 — Ralph control loop

- Persist iteration state on the active task JSON (`ralph_state`)
- Implement acceptance judge + fingerprint stuck detection
- Metacognition gate: PROCEED / REQUEST_FIX / COMPLETE / ABORT
- Emit fix tasks + dependency wait

### Step 3 — Fixture + demo task

- Add `fixtures/sample-app`
- `create_test_task.py` seeds a `ralph_ui_loop` task
- Document expected folder artifacts after a green run

### Step 4 — Visual baselines + optional recording

- Baseline store under `workspace/baselines/ui/` (or repo `baselines/`)
- Optional session video for failed runs only (cost/space)

### Step 5 — Wire into setup + docs

- `setup_multi_agent.py` knows the new agent
- Update `outline/agent-types-needed.md`, README next-steps, QUICK_REFERENCE
- Optional: `tasks/waiting/` support in `BaseAgent`

### Step 6 — Point at real ORC UI (when it exists)

- Replace fixture `base_url` with monitoring UI
- Encode product acceptance (brand, hero budget, mobile) as `acceptance[]`

---

## Exit Criteria for This Workstream

Done when:

1. `ScreenUIAgent` can claim a `ralph_ui_loop` task and drive a real browser
2. Screenshots + `report.json` land under `workspace/results/ui/`
3. Loop retries on failure and stops on pass / budget / stuck fingerprint
4. Failed asserts can spawn FileAgent fix tasks and resume after deps complete
5. Fixture demo is reproducible from QUICK_REFERENCE commands
6. Unit-style tests stay on `TestAgent` — no conflation

---

## Non-Goals

- Replacing Playwright with pure LLM clicking for core CI paths
- Full visual regression suite for every route on day one
- Automatic baseline updates without an explicit task flag
- Testing native mobile apps (browser/viewport only in v1)
- Building the entire monitoring product UI inside this plan (only fixtures + harness)

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Flaky selectors | Prefer `data-testid`; explicit waits; ban raw sleep except backoff |
| Headless vs headed diffs | Pin viewport, locale, timezone; use `device_scale_factor=1` |
| Infinite fix loops | Fingerprint + max_iterations + metacognition ABORT |
| LLM rubber-stamping PASS | Deterministic asserts required; vision only when flagged |
| Orphan browsers / ports | `finally` teardown; health checks; unique debug ports per run |
| Large artifacts | Keep last N iterations; video on fail only |

---

## Example Operator Flow

```bash
# Terminal A — Screen UI agent
cd screen-ui-agent && python3 run_autonomous.py

# Terminal B — File + Terminal agents (for fixes / server start)
cd file-agent && python3 run_autonomous.py
cd terminal-agent && python3 run_autonomous.py

# Seed a Ralph UI verification task
cd screen-ui-agent && python3 create_test_task.py

# Watch
ls workspace/tasks/active/
ls workspace/results/ui/
```

Success looks like: task in `completed/`, `report.json` with all acceptance `pass`, screenshots for each iteration, no orphan Chromium processes.

---

## Open Decisions

1. **Waiting folder** — add `tasks/waiting/` vs keep parent in `active/` with a `status: waiting_on_deps` field
2. **Vision judge** — Gemini vision on screenshots for design-rule criteria, or defer to pixel baselines only for v1
3. **Same process vs sidecar** — Playwright in-process in ScreenUIAgent (simpler) vs TerminalAgent-invoked CLI runner (stronger isolation)
4. **Baseline authority** — repo-committed baselines vs generated per environment

Recommendation defaults: **status field on active task**, **pixel baselines in v1 + optional vision later**, **in-process Playwright**, **repo-committed baselines**.
