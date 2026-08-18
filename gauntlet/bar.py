from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from .models import QualityBar


VAGUE_BAR_MARKERS = (
    "award-winning",
    "best in class",
    "world-class",
    "premium",
    "modern",
    "beautiful",
    "high quality",
    "industry standard",
    "good design",
)


def validate_bar(bar: QualityBar) -> Optional[str]:
    """Return an error string if the bar is not named, fetchable, and comparable."""
    name = (bar.name or "").strip()
    source = (bar.source or "").strip()
    medium = (bar.medium or "").strip()

    if len(name) < 8:
        return "Bar must be named: a specific artifact, not a category."
    lowered = name.lower()
    if any(marker in lowered for marker in VAGUE_BAR_MARKERS) and "http" not in source:
        if not Path(source).exists() and not source.startswith(("http://", "https://")):
            return "Bar looks vague. Name a real page, post, repo, or file the critic can open."
    if not source:
        return "Bar must be fetchable: a path or URL the critic can actually open."
    if source.startswith(("http://", "https://")):
        pass
    elif not Path(source).exists():
        return f"Bar is not fetchable: {source} does not exist on disk."
    if medium not in {"html", "text", "screenshot", "binary"}:
        return "Bar must be comparable in a concrete medium (html, text, screenshot, binary)."
    return None


def load_text(source: str) -> str:
    path = Path(source)
    if path.exists():
        return path.read_text(encoding="utf-8")
    if source.startswith(("http://", "https://")):
        raise FileNotFoundError("Network bars must be fetched by the caller and stored on disk.")
    raise FileNotFoundError(source)


def evidence_ok(artifact: str, medium: str) -> bool:
    if not artifact or not artifact.strip():
        return False
    if medium == "html":
        return "<html" in artifact.lower() and bool(re.search(r"<body[\s>]", artifact, re.I))
    return len(artifact.strip()) >= 40


def extract_preview(html: str, width: int = 36) -> str:
    """Turn inspectable HTML into a compact first-viewport sketch for the TUI."""
    if not html.strip():
        return "(empty)"

    def grab(pattern: str) -> str:
        match = re.search(pattern, html, re.I | re.S)
        return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""

    title = grab(r"<h1[^>]*>(.*?)</h1>")
    lede = grab(r"<p[^>]*class=['\"]lede['\"][^>]*>(.*?)</p>") or grab(r"<p[^>]*>(.*?)</p>")
    cta = grab(r"<a[^>]*data-cta=['\"]primary['\"][^>]*>(.*?)</a>") or grab(
        r"<button[^>]*>(.*?)</button>"
    )
    inner = width - 2
    lines = ["┌" + "─" * inner + "┐"]

    def row(text: str, emphasize: bool = False) -> None:
        clipped = text[: inner - 2]
        pad = inner - 2 - len(clipped)
        mark = "▸ " if emphasize else "  "
        lines.append("│" + mark + clipped + (" " * pad) + "│")

    row(title or "(no hero)")
    if lede:
        row(lede)
    if cta:
        row("[" + cta + "]", emphasize=True)
    lines.append("└" + "─" * inner + "┘")
    return "\n".join(lines)


def workspace_root() -> Path:
    env = os.getenv("WORKSPACE_PATH")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "workspace"
