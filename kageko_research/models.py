"""State models for deep research workflow."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, kw_only=True)
class TodoItem:
    id: int
    title: str
    intent: str
    query: str
    status: str = "pending"
    summary: str | None = None
    sources_summary: str | None = None
    note_path: str | None = None


@dataclass(slots=True, kw_only=True)
class ResearchState:
    research_topic: str
    todo_items: list[TodoItem] = field(default_factory=list)
    running_summary: str | None = None
    report_markdown: str | None = None
