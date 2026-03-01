#!/usr/bin/env python3
"""Utilities for resolving the Unreal MCP Python server directory."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def _candidate_dirs() -> Iterable[Path]:
    env_value = os.environ.get("UNREAL_MCP_PY_DIR")
    if env_value:
        yield Path(env_value).expanduser()

    # If a script is run via `uv --directory <mcp_dir> run ...`, cwd is already the MCP dir.
    cwd = Path.cwd()
    if (cwd / "unreal_mcp_server_advanced.py").exists():
        yield cwd

    # Legacy path used in this workspace on macOS.
    legacy = Path.home() / "Desktop" / "03_Projects" / "unreal" / "unreal-engine-mcp" / "Python"
    yield legacy


def resolve_mcp_py_dir() -> Path:
    for candidate in _candidate_dirs():
        candidate = candidate.resolve()
        if (candidate / "unreal_mcp_server_advanced.py").exists():
            return candidate

    raise FileNotFoundError(
        "Unable to find Unreal MCP Python directory.\n"
        "Set UNREAL_MCP_PY_DIR to <path>/unreal-engine-mcp/Python."
    )

