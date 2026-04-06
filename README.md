# Kageko Deep Research App

Full **backend + frontend** deep-research agent app built with `KagekoO_O` framework (add it as a gitsubmodule here).

## Quick Start

```
git clone 
cd KagekoResearch
git submodule update --init --recursive
python -m pip install -e .
```
Then you should create a .env file following:
```env
KAGEKO_PROVIDER="opeai"
KAGEKO_API_KEY=
KAGEKO_MODEL="gpt-4.1-mini"
KAGEKO_BASE_URL=

SEARCH_API="duckduckgo"
MAX_WEB_RESEARCH_LOOPS="3"
MAX_RESULTS_PER_QUERY="5"
ENABLE_NOTES="true"
NOTES_WORKSPACE="./workspace/notes"
REPORTS_WORKSPACE="./workspace/reports"
```

Then run it with:
```
python -m uvicorn kageko_research.main:app --host 127.0.0.1 --port 8012 --reload
```

Open: `http://127.0.0.1:8012`

If you hit `WinError 10013`, use another local port:

```powershell
python -m uvicorn kageko_research.main:app --host 127.0.0.1 --port 8088 --reload
```

## What You Get

1. **Frontend UI** (served by backend):
   - modern workspace layout (sidebar + live workflow + report panel)
   - quick topic presets, keyboard shortcuts, run/stop/reset controls
   - task board with progress meter, statuses, summaries, and sources
   - activity stream timeline with auto-scroll toggle
   - report viewer with rendered/raw toggle, copy, and markdown download
2. **Backend API**:
   - `GET /healthz`
   - `POST /research`
   - `POST /research/stream`
   - `GET /research/stream/get` (SSE-friendly for browser EventSource)
3. **TODO-driven workflow**:
   - planning (3-5 tasks)
   - multi-round search per task
   - summarization
   - final report generation
4. **Persistence**:
   - `workspace/notes/*.md` task notes
   - `workspace/reports/*.md` final reports

## Project Layout
```text
KagekoResearch/
├── KagekoO_O/                    # framework submodule
├── frontend/                     # browser UI (HTML/CSS/JS)
├── kageko_research/              # backend app
│   ├── main.py                   # FastAPI + static serving
│   ├── agent.py                  # deep-research orchestrator
│   └── services/                 # planner/search/summarizer/reporter/notes
└── pyproject.toml
```

