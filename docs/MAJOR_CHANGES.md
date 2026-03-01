# Major Changes Log

## 2026-03-01

### UnrealMCP Plugin Extensions (C++)
Added new editor command handlers to `Plugins/UnrealMCP`:
- `set_actor_tags`
- `set_actor_label`
- `set_light_properties`
- `add_text_render_component`
- `save_current_level`
- `save_current_level_as`
- `load_level`
- `new_blank_level`

Also extended `get_actors_in_level` filtering:
- `actor_type`
- `name_contains`
- `max_results`

### Python MCP Server Surface (external MCP repo)
Extended `unreal_mcp_server_advanced.py` tool wrappers for the new commands:
- `set_actor_tags`
- `set_actor_label`
- `set_light_properties`
- `add_text_render_component`
- `save_current_level`
- `save_current_level_as`
- `load_level`
- `new_blank_level`
- improved `get_actors_in_level` filters

### Lighting Stabilization
- Updated `tools/fix_hub_lighting.py` to use one directional light policy to avoid:
  - "Multiple directional lights are competing to be the single one used for forward shading..."
- Existing extra directional light in active map was removed through MCP.

### Cross-Platform Script Hardening
- Removed hard-coded macOS paths from `tools/` scripts.
- Added environment-based path resolution via `UNREAL_MCP_PY_DIR`.
- Added shared helper `tools/mcp_path.py`.
- Added Windows wrapper `tools/unreal_mcp_exec.ps1`.

### Repository Readiness
- Added Unreal `.gitignore` to prevent committing transient build/cache files.
- Added root `README.md`.

