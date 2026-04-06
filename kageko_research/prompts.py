"""Prompt templates for planner, summarizer and reporter."""

from __future__ import annotations

from datetime import datetime


def current_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def planner_prompt(*, topic: str) -> str:
    return f"""
You are a research planning expert.
Current date: {current_date()}
Research topic: {topic}

Decompose the topic into 3-5 tasks.
Each task must include:
- title
- intent
- query

Return JSON only in this format:
{{
  "tasks": [
    {{"title": "...", "intent": "...", "query": "..."}}
  ]
}}
"""


def summarizer_prompt(
    *, topic: str, task_title: str, task_intent: str, query: str, search_context: str
) -> str:
    return f"""
You are a task summarization expert.
Research topic: {topic}
Task title: {task_title}
Task intent: {task_intent}
Search query: {query}

Search results:
{search_context}

Write a Markdown summary with:
1. Core viewpoints
2. Key data
3. Sources section with citations
4. Preserve important numbers, dates and names
"""


def reporter_prompt(*, topic: str, task_blocks: str) -> str:
    return f"""
You are a report writing expert.
Research topic: {topic}

Task summaries:
{task_blocks}

Generate a Markdown report with:
1. Title
2. Overview
3. Detailed analysis per task
4. Summary
5. References
"""
