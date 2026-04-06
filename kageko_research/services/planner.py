"""Task planning service."""

from __future__ import annotations

import json
import re

from ..models import ResearchState, TodoItem
from ..prompts import planner_prompt


class PlanningService:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def plan(self, state: ResearchState) -> list[TodoItem]:
        response = self.runtime.run(
            "chat",
            planner_prompt(topic=state.research_topic),
        )
        tasks = self._extract_tasks(response.text)
        items: list[TodoItem] = []
        for idx, task in enumerate(tasks, start=1):
            items.append(
                TodoItem(
                    id=idx,
                    title=str(task.get("title", f"Task {idx}")).strip(),
                    intent=str(task.get("intent", "Investigate key aspects")).strip(),
                    query=str(task.get("query", state.research_topic)).strip(),
                )
            )
        if len(items) < 3:
            return []
        return items[:5]

    def _extract_tasks(self, text: str) -> list[dict]:
        object_candidate = self._extract_json_object(text)
        if object_candidate is not None:
            tasks = object_candidate.get("tasks")
            if isinstance(tasks, list):
                return [x for x in tasks if isinstance(x, dict)]

        array_candidate = self._extract_json_array(text)
        if isinstance(array_candidate, list):
            return [x for x in array_candidate if isinstance(x, dict)]

        return []

    @staticmethod
    def _extract_json_object(text: str) -> dict | None:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text[start : end + 1]
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _extract_json_array(text: str) -> list | None:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, list) else None

