# SignalBound

Unreal Engine 5.7 project for the SignalBound world build and MCP-driven editor automation.

## What Is In This Repo
- Unreal project: `SignalBound.uproject`
- Unreal MCP plugin source (extended): `Plugins/UnrealMCP/`
- MCP helper scripts: `tools/`
- Specs + architecture + continuity docs: `docs/`

## Quick Status
- Hub graybox and markers are in progress in-editor via MCP workflows.
- MCP plugin command surface has been extended in C++ for:
  - actor tags
  - actor labels
  - light property updates
  - text render component placement
  - map save/load/new helpers
- Lighting warning fixed in current map by enforcing one directional light.

## Cross-Platform Setup (macOS + Windows)
1. Install Unreal Engine 5.7.
2. Open `SignalBound.uproject` once so Unreal builds project/plugin binaries.
3. Clone `unreal-engine-mcp` (the Python MCP server repo) somewhere on disk.
4. Install Python 3.13 and `uv`.
5. Set environment variable `UNREAL_MCP_PY_DIR` to `<path>/unreal-engine-mcp/Python`.
6. Restart Unreal Editor after any `Plugins/UnrealMCP` C++ changes.

## Windows Notes
- The helper scripts are now path-portable through `UNREAL_MCP_PY_DIR`.
- Use PowerShell wrapper:
  - `tools/unreal_mcp_exec.ps1 ping '{}'`
- If Unreal shows old MCP command behavior, plugin hot-reload did not pick up C++ changes:
  - close editor
  - reopen project
  - let plugin recompile

## MCP Helper Commands
- Ping:
  - `tools/unreal_mcp_exec.sh ping '{}'`
- Find actor:
  - `tools/unreal_mcp_exec.sh find_actors_by_name '{"pattern":"BP_SafeNode_00"}'`
- Run hub builder phase:
  - `uv --directory "$UNREAL_MCP_PY_DIR" run python tools/build_signalbound_hub.py --phase markers`
- Lighting pass:
  - `uv --directory "$UNREAL_MCP_PY_DIR" run python tools/fix_hub_lighting.py`

## Continuity
- Current handoff: `docs/SESSION_HANDOFF_2026-03-01.md`
- Major changes log: `docs/MAJOR_CHANGES.md`
- Hub map progress doc: `docs/MAP_HUB_PROGRESS_2026-03-01.md`
- Project execution conventions: `CLAUDE.md`
