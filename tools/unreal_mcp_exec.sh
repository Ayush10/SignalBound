#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

UV_BIN="${UV_BIN:-$(command -v uv || true)}"
if [[ -z "${UV_BIN}" ]]; then
  echo "ERROR: uv is not installed or not in PATH." >&2
  exit 127
fi

MCP_PY_DIR="${UNREAL_MCP_PY_DIR:-}"
if [[ -z "${MCP_PY_DIR}" ]]; then
  LEGACY="${HOME}/Desktop/03_Projects/unreal/unreal-engine-mcp/Python"
  if [[ -f "${LEGACY}/unreal_mcp_server_advanced.py" ]]; then
    MCP_PY_DIR="${LEGACY}"
  else
    echo "ERROR: UNREAL_MCP_PY_DIR is not set and no default MCP path was found." >&2
    echo "Set UNREAL_MCP_PY_DIR to your unreal-engine-mcp/Python path." >&2
    exit 2
  fi
fi

"${UV_BIN}" --directory "${MCP_PY_DIR}" run python "${SCRIPT_DIR}/unreal_mcp_exec.py" "$@"
