# AGENTS.md

## Cursor Cloud specific instructions

This repo is the **Multi-Agent Orchestration System (ORC)** — a single product organized as a
monorepo of Python agents built on Google's Agent Development Kit (ADK). Each `*-agent/` directory
is a self-contained autonomous process. There is **no central server, database, or message broker**;
agents coordinate purely through the shared `workspace/` directory (JSON task files flow through
`workspace/tasks/{pending,active,completed,failed}/`).

### Runtime prerequisite (non-obvious, important)
- **Every agent requires a valid `GOOGLE_API_KEY` (Gemini) to do anything.** Each agent drives three
  Gemini `gemini-2.0-flash` LLMs (executor / evaluator / metacognition) via ADK. Without a valid key,
  agents still start and detect tasks but every LLM call fails with `400 API_KEY_INVALID`, so no task
  is ever claimed or completed. Set `GOOGLE_API_KEY` in the environment (or in the root `.env`).
  Alternatively use Vertex AI by setting `GOOGLE_GENAI_USE_VERTEXAI=TRUE` plus the related
  `GOOGLE_CLOUD_*` vars.
- `run_autonomous.py` hard-exits at startup if neither `GOOGLE_API_KEY` nor `GOOGLE_GENAI_USE_VERTEXAI`
  is set.

### First-time / per-session setup
- Dependencies (`google-adk`, `python-dotenv`, and optional `gspread`/`pandas`) are installed by the
  Cloud Agent update script; no manual install needed. A `requirements.txt` is also provided.
- Run `python3 setup_multi_agent.py` once to create the `workspace/` tree and copy `.env.example` to
  `.env`. Runners also auto-create the `workspace/` tree on start, so this is optional.
- `.env` and `workspace/` are gitignored (runtime-only, never commit them).

### Running the system
- Standard run/test commands live in `README.md` and `QUICK_REFERENCE.md`. Summary: start each agent
  as its own long-lived process, e.g. `cd file-agent && python3 run_autonomous.py`. The 4 core agents
  are `task-breakdown-agent`, `google-search-agent`, `file-agent`, `terminal-agent`. Optional agents:
  `git-agent`, `test-agent`, `database-agent`, `api-agent`, `google-sheets-agent`.
- Only `google-sheets-agent` needs extra deps (`gspread`, `pandas`) and optionally
  `GOOGLE_SERVICE_ACCOUNT_FILE` (it degrades gracefully if absent).
- Create a task with `python3 create_test_task.py` (root or per-agent), or drop a JSON file into
  `workspace/tasks/pending/`. Agents poll continuously and claim tasks atomically via `os.rename()`.
- Use `python3 -u ...` for unbuffered output when watching an agent's log — stdout is otherwise
  buffered and ADK error tracebacks (stderr) can otherwise appear before the agent's own log lines.

### Lint / test / build
- There is **no build step** (plain Python), and the repo has **no configured linter or test
  framework** (no pytest/flake8/ruff/mypy config, no CI). A syntax-level check is
  `python3 -m compileall <files>`.
