"""Orchestrator for TODO-driven deep research workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .bootstrap import create_runtime, load_environment
from .config import Configuration
from .models import ResearchState, TodoItem
from .services.notes import NotesService
from .services.planner import PlanningService
from .services.reporter import ReportingService
from .services.search import (
    format_for_prompt,
    search_multi_round,
    sources_summary,
)
from .services.summarizer import SummarizationService


@dataclass(slots=True, kw_only=True)
class DeepResearchResult:
    report_markdown: str
    todo_items: list[TodoItem]
    report_path: str | None = None


class DeepResearchAgent:
    def __init__(self, *, config: Configuration | None = None) -> None:
        load_environment()
        self.config = config or Configuration.from_env()

        self.runtime = create_runtime(
            provider=self.config.llm_provider,
            api_key=self.config.llm_api_key,
            model=self.config.llm_model,
            base_url=self.config.llm_base_url,
        )

        self.planner = PlanningService(self.runtime)
        self.summarizer = SummarizationService(self.runtime)
        self.reporter = ReportingService(self.runtime)
        self.notes = NotesService(
            notes_workspace=self.config.notes_workspace,
            reports_workspace=self.config.reports_workspace,
        )

    def run(self, topic: str) -> DeepResearchResult:
        state = self._init_state(topic)
        self._execute(state)
        report = self.reporter.generate_report(topic=state.research_topic, tasks=state.todo_items)
        state.report_markdown = report
        report_path = self.notes.save_final_report(topic=topic, report=report)
        return DeepResearchResult(
            report_markdown=report,
            todo_items=state.todo_items,
            report_path=report_path,
        )

    def run_stream(self, topic: str) -> Iterator[dict]:
        yield {"type": "status", "message": "Planning tasks"}
        state = self._init_state(topic)
        yield {"type": "todo_list", "tasks": [self._serialize_task(t) for t in state.todo_items]}

        for task in state.todo_items:
            task.status = "in_progress"
            yield {"type": "task_status", "task_id": task.id, "status": task.status, "title": task.title}

            results, round_queries = search_multi_round(task.query, config=self.config)
            formatted = format_for_prompt(results)
            task.sources_summary = sources_summary(results)
            yield {
                "type": "sources",
                "task_id": task.id,
                "sources_summary": task.sources_summary,
                "round_queries": round_queries,
            }

            summary = self.summarizer.summarize(
                topic=state.research_topic,
                task_title=task.title,
                task_intent=task.intent,
                query=task.query,
                search_context=formatted,
            )
            task.summary = summary
            if self.config.enable_notes:
                task.note_path = self.notes.save_task_note(
                    task=task,
                    round_queries=round_queries,
                    search_results=results,
                    summary=summary,
                )

            yield {"type": "task_summary_chunk", "task_id": task.id, "content": task.summary}
            task.status = "completed"
            yield {
                "type": "task_status",
                "task_id": task.id,
                "status": task.status,
                "summary": task.summary,
                "note_path": task.note_path,
            }

        report = self.reporter.generate_report(topic=state.research_topic, tasks=state.todo_items)
        state.report_markdown = report
        report_path = self.notes.save_final_report(topic=topic, report=report)
        yield {"type": "final_report", "report": report, "report_path": report_path}
        yield {"type": "done"}

    def _init_state(self, topic: str) -> ResearchState:
        state = ResearchState(research_topic=topic)
        state.todo_items = self.planner.plan(state)
        if not state.todo_items:
            state.todo_items = [
                TodoItem(
                    id=1,
                    title="Background research",
                    intent="Collect core background and latest updates",
                    query=topic,
                )
            ]
        return state

    def _execute(self, state: ResearchState) -> None:
        for task in state.todo_items:
            task.status = "in_progress"
            results, round_queries = search_multi_round(task.query, config=self.config)
            context = format_for_prompt(results)
            summary = self.summarizer.summarize(
                topic=state.research_topic,
                task_title=task.title,
                task_intent=task.intent,
                query=task.query,
                search_context=context,
            )
            task.summary = summary
            task.sources_summary = sources_summary(results)
            if self.config.enable_notes:
                task.note_path = self.notes.save_task_note(
                    task=task,
                    round_queries=round_queries,
                    search_results=results,
                    summary=summary,
                )
            task.status = "completed"

    @staticmethod
    def _serialize_task(task: TodoItem) -> dict:
        return {
            "id": task.id,
            "title": task.title,
            "intent": task.intent,
            "query": task.query,
            "status": task.status,
            "summary": task.summary,
            "sources_summary": task.sources_summary,
            "note_path": task.note_path,
        }

