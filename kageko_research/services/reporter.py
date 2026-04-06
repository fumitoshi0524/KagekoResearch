"""Final report generation service."""

from __future__ import annotations

from ..models import TodoItem
from ..prompts import reporter_prompt


class ReportingService:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def generate_report(self, *, topic: str, tasks: list[TodoItem]) -> str:
        blocks: list[str] = []
        for task in tasks:
            blocks.append(
                "\n".join(
                    [
                        f"## Task {task.id}: {task.title}",
                        f"Intent: {task.intent}",
                        f"Query: {task.query}",
                        "Summary:",
                        task.summary or "N/A",
                        "Sources:",
                        task.sources_summary or "N/A",
                    ]
                )
            )

        response = self.runtime.run(
            "chat",
            reporter_prompt(
                topic=topic,
                task_blocks="\n\n".join(blocks),
            ),
        )
        return response.text.strip()
