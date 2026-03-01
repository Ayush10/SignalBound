#!/usr/bin/env python3
"""Run a single Unreal MCP command against the Unreal Editor socket bridge."""

import argparse
import json
import os
import sys
from pathlib import Path

from mcp_path import resolve_mcp_py_dir


def load_server_module(mcp_py_dir: str):
    mcp_path = Path(mcp_py_dir).expanduser().resolve()
    if not mcp_path.exists():
        raise FileNotFoundError(
            f"MCP Python directory not found: {mcp_path}\n"
            "Set UNREAL_MCP_PY_DIR to <path>/unreal-engine-mcp/Python."
        )

    if str(mcp_path) not in sys.path:
        sys.path.insert(0, str(mcp_path))

    import unreal_mcp_server_advanced as server  # type: ignore

    return server


def parse_params(raw: str):
    if raw.startswith("@"):
        params_file = Path(raw[1:]).expanduser().resolve()
        if not params_file.exists():
            raise FileNotFoundError(f"Params file not found: {params_file}")
        return json.loads(params_file.read_text(encoding="utf-8"))

    return json.loads(raw)


def main() -> int:
    default_mcp_py_dir = os.environ.get("UNREAL_MCP_PY_DIR")
    if not default_mcp_py_dir:
        try:
            default_mcp_py_dir = str(resolve_mcp_py_dir())
        except FileNotFoundError:
            # Keep arg optional and fail later with a clearer error in load_server_module.
            default_mcp_py_dir = ""

    parser = argparse.ArgumentParser(
        description="Send a raw command to the Unreal MCP socket bridge."
    )
    parser.add_argument("command", help="Unreal command type, e.g. get_actors_in_level")
    parser.add_argument(
        "params",
        nargs="?",
        default="{}",
        help="JSON params object or @/path/to/params.json (default: {})",
    )
    parser.add_argument(
        "--mcp-py-dir",
        default=default_mcp_py_dir,
        help="Path to unreal-engine-mcp/Python",
    )
    args = parser.parse_args()

    try:
        params = parse_params(args.params)
        if not isinstance(params, dict):
            raise ValueError("params JSON must be an object")
    except Exception as exc:
        print(json.dumps({"status": "error", "error": f"Invalid params: {exc}"}))
        return 2

    try:
        server = load_server_module(args.mcp_py_dir)
        unreal = server.get_unreal_connection()
        response = unreal.send_command(args.command, params)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 3

    if response is None:
        print(json.dumps({"status": "error", "error": "No response from Unreal"}))
        return 4

    print(json.dumps(response, indent=2))
    return 0 if response.get("status") != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
