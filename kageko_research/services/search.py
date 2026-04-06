"""Search scheduling service."""

from __future__ import annotations

from datetime import datetime

from ddgs import DDGS

from ..config import Configuration
from .utils import dedupe_by_url, limit_text


def search(query: str, *, config: Configuration) -> list[dict]:
    if config.search_api.value != "duckduckgo":
        raise ValueError(f"Unsupported search backend: {config.search_api.value}")

    with DDGS() as ddgs:
        results = list(
            ddgs.text(
                query,
                max_results=config.max_results_per_query,
            )
        )

    normalized: list[dict] = []
    for item in results:
        title = str(item.get("title", "")).strip()
        url = str(item.get("href", item.get("url", ""))).strip()
        snippet = str(item.get("body", item.get("snippet", ""))).strip()
        normalized.append(
            {
                "title": title,
                "url": url,
                "snippet": limit_text(snippet, max_chars=2000),
            }
        )
    return dedupe_by_url(normalized)


def format_for_prompt(results: list[dict]) -> str:
    blocks: list[str] = []
    for i, item in enumerate(results, start=1):
        blocks.append(
            "\n".join(
                [
                    f"[{i}] {item.get('title', '')}",
                    f"URL: {item.get('url', '')}",
                    f"Snippet: {item.get('snippet', '')}",
                ]
            )
        )
    return "\n\n".join(blocks).strip()


def sources_summary(results: list[dict]) -> str:
    return "\n".join(
        f"- {item.get('title', '')}: {item.get('url', '')}"
        for item in results
        if item.get("url")
    )


def build_round_queries(query: str, *, max_loops: int) -> list[str]:
    year = datetime.now().year
    candidates = [
        query,
        f"{query} latest",
        f"{query} {year}",
        f"{query} benchmark",
        f"{query} engineering practice",
        f"{query} risks",
    ]

    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = candidate.strip()
        if normalized == "" or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique[:max_loops]


def search_multi_round(
    query: str, *, config: Configuration
) -> tuple[list[dict], list[str]]:
    round_queries = build_round_queries(
        query,
        max_loops=config.max_web_research_loops,
    )
    merged: list[dict] = []
    for round_query in round_queries:
        merged.extend(search(round_query, config=config))
    return dedupe_by_url(merged), round_queries
