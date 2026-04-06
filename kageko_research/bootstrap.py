"""Bootstrap helpers for loading KagekoO_O runtime from submodule."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _framework_root() -> Path:
    return _project_root() / "KagekoO_O"


def ensure_framework_on_path() -> None:
    framework_root = _framework_root()
    framework_parent = str(framework_root.parent)
    if framework_parent not in sys.path:
        sys.path.insert(0, framework_parent)


_POWERSHELL_ENV_PATTERN = re.compile(
    r"\$env:([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\r\n$#]+))"
)


def _load_powershell_style_env(dotenv_path: Path) -> None:
    try:
        content = dotenv_path.read_text(encoding="utf-8")
    except OSError:
        return

    for match in _POWERSHELL_ENV_PATTERN.finditer(content):
        key = match.group(1)
        value = match.group(2) or match.group(3) or match.group(4) or ""
        value = value.strip()
        if value:
            os.environ.setdefault(key, value)


def load_environment() -> None:
    from dotenv import find_dotenv, load_dotenv

    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path, override=False)
        _load_powershell_style_env(Path(dotenv_path))
    else:
        load_dotenv(override=False)


class RuntimeFacade:
    def __init__(self, runtime) -> None:
        self._runtime = runtime

    def run(
        self, mode: str, message: str, session_id: str | None = None, tool_plan=None
    ):
        ensure_framework_on_path()
        from KagekoO_O import AgentMode

        mode_value = AgentMode(mode)
        return self._runtime.run(
            mode_value, message, session_id=session_id, tool_plan=tool_plan
        )


def create_runtime(
    *,
    provider: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
):
    ensure_framework_on_path()
    from KagekoO_O import create_runtime as _create_runtime

    workspace = (_project_root() / "workspace").resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    runtime = _create_runtime(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        workspace=str(workspace),
    )
    return RuntimeFacade(runtime)
