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

### Hub Map Recovery + Rebuild
- Diagnosed map mismatch where only a floating-island/template scene was visible.
- Confirmed hub prefixes were absent in the active map, then cleaned template actors.
- Rebuilt hub districts and markers in the active level using phased script runs.
- Re-verified required marker presence and district actor counts.
- Added full map continuity record:
  - `docs/MAP_HUB_PROGRESS_2026-03-01.md`

### Hub Vibrant Visual Pass
- Added `tools/beautify_hub_vibrant.py` for colorful city dressing.
- Applied vibrant material accents across hub hero pieces.
- Added flower-rich beautification set:
  - ribbon accents
  - planters + soil beds
  - rose/flower stems, blooms, buds
  - garden glow point lights

### Additive-Safe Build Hardening
- Updated hub build scripts to preserve existing actors by default:
  - `tools/build_hub_citadel_city_v2.py`
  - `tools/build_signalbound_hub.py`
  - `tools/beautify_hub_vibrant.py`
- Added explicit opt-in safety flags:
  - `--allow-clear` for destructive cleanup
  - `--overwrite-existing` for intentional replacement
- Default behavior now skips existing actor names instead of deleting them.

### Metropolis Expansion (Partial, Additive)
- Successfully added phases:
  - `core`
  - `contract_vista`
  - `signal_quarter`
- Remaining phases intentionally left for continuation:
  - `skyline`
  - `vehicles`
  - `arenas_outskirts`
  - `undercroft`
  - `markers_plaques`
- Handoff doc created for Windows continuation:
  - `docs/WINDOWS_HANDOFF_HUB_ADDITIVE_2026-03-01.md`
