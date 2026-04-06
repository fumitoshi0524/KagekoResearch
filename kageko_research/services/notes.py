"""Filesystem note/report persistence helpers."""

from __future__ import annotations

import re
from pathlib import Path

from ..models import TodoItem
from .utils import ensure_dir


def _slug(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text).strip("-")
    return normalized[:60] or "task"


class NotesService:
    def __init__(self, *, notes_workspace: str, reports_workspace: str) -> None:
        self.notes_dir = ensure_dir(notes_workspace)
        self.reports_dir = ensure_dir(reports_workspace)

    def save_task_note(
        self,
        *,
        task: TodoItem,
        round_queries: list[str],
        search_results: list[dict],
        summary: str,
    ) -> str:
        filename = f"{task.id:02d}-{_slug(task.title)}.md"
        path = self.notes_dir / filename

        lines: list[str] = [
            f"# Task {task.id}: {task.title}",
            "",
            "## Task Info",
            "",
            f"- Intent: {task.intent}",
            f"- Query: {task.query}",
            "",
            "## Search Rounds",
            "",
        ]
        for i, round_query in enumerate(round_queries, start=1):
            lines.append(f"{i}. {round_query}")
        lines.extend(
            [
                "",
            "## Search Results",
            "",
            ]
        )
        for i, item in enumerate(search_results, start=1):
            lines.append(f"[{i}] {item.get('title', '')}")
            lines.append(f"URL: {item.get('url', '')}")
            lines.append(f"Snippet: {item.get('snippet', '')}")
            lines.append("")

        lines.extend(["## Summary", "", summary.strip(), ""])
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    def save_final_report(self, *, topic: str, report: str) -> str:
        filename = f"{_slug(topic)}-final-report.md"
        path = self.reports_dir / filename
        path.write_text(report.strip() + "\n", encoding="utf-8")
        return str(path)

