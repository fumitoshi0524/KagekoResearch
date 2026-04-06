"""Utility helpers for service layer."""

from __future__ import annotations

from pathlib import Path


def ensure_dir(path: str) -> Path:
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def dedupe_by_url(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        url = str(item.get("url", "")).strip()
        if url == "" or url in seen:
            continue
        seen.add(url)
        unique.append(item)
    return unique


def limit_text(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."

