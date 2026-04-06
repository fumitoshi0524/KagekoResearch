"""FastAPI entrypoint for Kageko deep research service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent import DeepResearchAgent
from .config import Configuration, SearchAPI


class ResearchRequest(BaseModel):
    topic: str = Field(..., description="Research topic")
    search_api: SearchAPI | None = Field(default=None)


class ResearchResponse(BaseModel):
    report_markdown: str
    report_path: str | None = None
    todo_items: list[dict[str, Any]]


def _build_config(payload: ResearchRequest) -> Configuration:
    return Configuration.from_env(
        overrides={
            "search_api": payload.search_api.value if payload.search_api else None,
        }
    )


def _stream_research_events(payload: ResearchRequest) -> Iterator[str]:
    try:
        config = _build_config(payload)
        agent = DeepResearchAgent(config=config)
    except ValueError as exc:
        error_payload = {"type": "error", "detail": str(exc)}
        yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"
        return

    try:
        for event in agent.run_stream(payload.topic):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    except Exception as exc:
        error_payload = {"type": "error", "detail": str(exc)}
        yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"


def create_app() -> FastAPI:
    app = FastAPI(title="Kageko Deep Research")
    frontend_dir = Path(__file__).resolve().parents[1] / "frontend"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/assets", StaticFiles(directory=str(frontend_dir)), name="assets")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def root() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")

    @app.post("/research", response_model=ResearchResponse)
    def run_research(payload: ResearchRequest) -> ResearchResponse:
        try:
            config = _build_config(payload)
            agent = DeepResearchAgent(config=config)
            result = agent.run(payload.topic)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Research failed") from exc

        todo_items = [
            {
                "id": item.id,
                "title": item.title,
                "intent": item.intent,
                "query": item.query,
                "status": item.status,
                "summary": item.summary,
                "sources_summary": item.sources_summary,
                "note_path": item.note_path,
            }
            for item in result.todo_items
        ]
        return ResearchResponse(
            report_markdown=result.report_markdown,
            report_path=result.report_path,
            todo_items=todo_items,
        )

    @app.post("/research/stream")
    def stream_research(payload: ResearchRequest) -> StreamingResponse:
        return StreamingResponse(
            _stream_research_events(payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    @app.get("/research/stream/get")
    def stream_research_get(request: Request) -> StreamingResponse:
        topic = request.query_params.get("topic")
        search_api_raw = request.query_params.get("search_api")
        if topic is None or topic.strip() == "":
            raise HTTPException(status_code=400, detail="topic is required")

        search_api = None
        if search_api_raw:
            try:
                search_api = SearchAPI(search_api_raw)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="invalid search_api") from exc

        payload = ResearchRequest(topic=topic, search_api=search_api)
        return StreamingResponse(
            _stream_research_events(payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("kageko_research.main:app", host="0.0.0.0", port=8000, reload=True)

