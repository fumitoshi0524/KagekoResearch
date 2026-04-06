"""Configuration for deep research application."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SearchAPI(str, Enum):
    DUCKDUCKGO = "duckduckgo"


def _to_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    lowered = value.strip().lower()
    return lowered in {"1", "true", "yes", "y", "on"}


class Configuration(BaseModel):
    llm_provider: str | None = Field(default=None)
    llm_api_key: str | None = Field(default=None)
    llm_base_url: str | None = Field(default=None)
    llm_model: str | None = Field(default=None)
    search_api: SearchAPI = Field(default=SearchAPI.DUCKDUCKGO)
    max_web_research_loops: int = Field(default=3, ge=1, le=8)
    max_results_per_query: int = Field(default=5, ge=1, le=10)
    notes_workspace: str = Field(default="./workspace/notes")
    reports_workspace: str = Field(default="./workspace/reports")
    enable_notes: bool = Field(default=True)

    @classmethod
    def from_env(cls, overrides: dict[str, Any] | None = None) -> "Configuration":
        data: dict[str, Any] = {
            "llm_provider": os.getenv("KAGEKO_PROVIDER"),
            "llm_api_key": os.getenv("KAGEKO_API_KEY") or os.getenv("OPENAI_API_KEY"),
            "llm_base_url": os.getenv("KAGEKO_BASE_URL"),
            "llm_model": os.getenv("KAGEKO_MODEL"),
            "search_api": os.getenv("SEARCH_API", SearchAPI.DUCKDUCKGO.value),
            "max_web_research_loops": int(os.getenv("MAX_WEB_RESEARCH_LOOPS", "3")),
            "max_results_per_query": int(os.getenv("MAX_RESULTS_PER_QUERY", "5")),
            "notes_workspace": os.getenv("NOTES_WORKSPACE", "./workspace/notes"),
            "reports_workspace": os.getenv("REPORTS_WORKSPACE", "./workspace/reports"),
            "enable_notes": _to_bool(os.getenv("ENABLE_NOTES"), default=True),
        }
        if overrides:
            for key, value in overrides.items():
                if value is not None:
                    data[key] = value
        return cls(**data)

