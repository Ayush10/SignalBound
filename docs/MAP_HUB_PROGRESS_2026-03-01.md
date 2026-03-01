# SignalBound Map Progress (Hub) - 2026-03-01

## Scope
This document captures map-related work completed so far for SignalBound, focused on `Map_HubCitadelCity`.

## Maps Status
- `Map_HubCitadelCity`: present (`Content/Map_HubCitadelCity.umap`)
- `Map_SystemTest`: missing as a saved map asset (not present as `Content/Map_SystemTest.umap`)

## What Was Done (Map Work)
1. Verified Unreal MCP connectivity and actor command execution against the running editor.
2. Built hub graybox+dressing districts via MCP script runs.
3. Placed required named markers and plaque actors.
4. Added and tuned lighting support for readability; enforced one-directional-light policy.
5. Investigated mismatch where only a floating-island/template scene was visible.
6. Removed floating-island/template actors from the active map.
7. Rebuilt hub districts in the currently loaded level and re-validated counts.
8. Applied vibrant beautification pass (color accents, ribbons, floral/rose gardens) on top of hub layout.

## District Build Coverage
Districts created in the active level:
- Grand Mirror Hall
- System Dais
- Armory + Archive
- Ascension Gallery
- Exterior ring + skyline
- Vista moment

## Verified Actor Counts (Current)
- `SM_GMH_`: 56
- `SM_SD_`: 20
- `SM_AA_`: 42
- `SM_AG_`: 36
- `SM_EXT_`: 140
- `SM_VISTA_`: 46
- `BP_PlayerStart_Map_HubCitadelCity`: 1
- `BP_SafeNode_00`: 1
- `BP_AscensionGate_00`: 1
- `BP_AscensionGate_01`: 1
- `BP_AscensionGate_02`: 1
- `BP_SystemNoticePlaque_`: 5
- `TagMarker_SpawnGroup_`: 10

Cleanup verification (floating island removed):
- `StaticMeshActor_UAID`: 0
- `Floor_UAID`: 0
- `L_FIX_`: 0

## Landmark Positions (Current)
- `SM_GMH_Floor_Main`: `[-8000, 0, -120]`
- `SM_SD_Dais_Main`: `[0, 0, 20]`
- `SM_AA_Armory_Floor`: `[3800, -7600, -110]`
- `SM_AG_Floor`: `[12800, 0, -100]`
- `SM_VISTA_BalconyBroken`: `[18200, 5200, 1450]`
- `BP_PlayerStart_Map_HubCitadelCity`: `[-14600, 0, 120]`
- `BP_SafeNode_00`: `[-13650, 600, 120]`
- `BP_AscensionGate_00`: `[12600, -3600, 20]`
- `BP_AscensionGate_01`: `[12600, 0, 20]`
- `BP_AscensionGate_02`: `[12600, 3600, 20]`

## Scripts Used
- `tools/build_signalbound_hub.py`
- `tools/fix_hub_lighting.py`
- `tools/beautify_hub_vibrant.py`
- `tools/unreal_mcp_exec.py`
- `tools/unreal_mcp_exec.sh`

## Vibrant Beautification Pass (Current)
High-level additions:
- Recolored key hero elements (glass/shards/ring/door-seals/canal accents)
- Added decorative ribbon rows in hall and terrace approach
- Added 12 flower/rose clusters across traversal path

Floral actor counts:
- `SM_GARDEN_Ribbon_`: 19
- `SM_GARDEN_Planter_`: 12
- `SM_GARDEN_Soil_`: 12
- `SM_FLOWER_Stem_`: 96
- `SM_Rose_`: 96
- `SM_FLOWER_Bud_`: 96
- `L_BEAUTY_GardenGlow_`: 12

Rose varieties currently placed:
- `CathedralWinchester`
- `SunflareRose`
- `IvoryLumin`
- `AuroraVelvet`

## Important Notes
- Hub visibility issue was map/session mismatch, not missing script logic.
- If the scene appears reset again, first confirm you are on `Map_HubCitadelCity`.
- Plugin command surface was extended in source, but newly added commands require editor/plugin reload before they are callable.

## Outstanding Map Items
1. Save and keep working in `Map_HubCitadelCity` as primary map.
2. Create and save `Map_SystemTest` as an actual `.umap`.
3. Replace proxy `TagMarker_SpawnGroup_*` with real actor tags using new MCP tag command after plugin reload.
4. Replace placeholder plaque setup with final visible text surfaces/materials if needed.

## Quick Resume Checklist
1. Open Unreal Editor and load `Map_HubCitadelCity`.
2. Confirm anchor actors exist (for example `SM_GMH_Floor_Main`, `BP_PlayerStart_Map_HubCitadelCity`).
3. If needed, rerun district phases from `tools/build_signalbound_hub.py`.
4. Save level immediately after any large build pass.
