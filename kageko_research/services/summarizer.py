"""Task summarization service."""

from __future__ import annotations

from ..prompts import summarizer_prompt


class SummarizationService:
    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def summarize(
        self,
        *,
        topic: str,
        task_title: str,
        task_intent: str,
        query: str,
        search_context: str,
    ) -> str:
        response = self.runtime.run(
            "chat",
            summarizer_prompt(
                topic=topic,
                task_title=task_title,
                task_intent=task_intent,
                query=query,
                search_context=search_context,
            ),
        )
        return response.text.strip()

