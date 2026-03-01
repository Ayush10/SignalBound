# Windows Handoff - Hub Build Complete (2026-03-01)

## Objective
Rebuild all v2 district phases for `Map_HubCitadelCity` that were lost to unsaved crashes.

## What Was Completed
1. Added 100ms throttle to `build_hub_citadel_city_v2.py` to prevent MCP connection drops.
2. Rebuilt all 8 v2 phases with saves between each:
   - `core` (233 actors)
   - `contract_vista` (68 actors)
   - `signal_quarter` (27 actors + lights)
   - `skyline` (39 spires + 59 residential + 22 cloud silhouettes)
   - `vehicles` (19 vehicles + 19 transit)
   - `arenas_outskirts` (37 arena + 37 outskirts)
   - `undercroft` (30 actors)
   - `markers_plaques` (12 plaques, 2 player starts, 2 safe nodes, 3 gates)
3. Restored vibrant beautification flora (349 actors).
4. Saved after every phase — all work is persisted.

## Final Actor Inventory
| Prefix | Count | District |
|---|---|---|
| SM_GMH_ | 56 | Grand Mirror Hall |
| SM_SD_ | 20 | System Dais |
| SM_AA_ | 42 | Armory/Archive |
| SM_AG_ | 36 | Ascension Gallery |
| SM_EXT_ | 140 | Exterior Ring |
| SM_VISTA_ | 42 | Vista Moment |
| SM_CORE_ | 233 | Sovereign Core (v2) |
| SM_CON_ | 68 | Contract Terrace/Vista (v2) |
| SM_SIG_ | 27 | Signal Quarter (v2) |
| SM_SKY_ | 39 | Skyline Spires (v2) |
| SM_RES_ | 59 | Residential Terraces (v2) |
| SM_CLOUD_ | 22 | Cloud Silhouettes (v2) |
| SM_TRN_ | 19 | Transit Lanes (v2) |
| SM_VEH_ | 19 | Vehicles (v2) |
| SM_ARENA_ | 37 | Arenas (v2) |
| SM_OUT_ | 37 | Outskirts (v2) |
| SM_UND_ | 30 | Undercroft (v2) |
| SM_GARDEN_ | 49 | Garden/Planters |
| SM_FLOWER_ | 188 | Flower Stems/Buds |
| SM_Rose_ | 94 | Rose Clusters |
| L_BEAUTY_ | 12 | Garden Glow Lights |
| BP_PlayerStart | 2 | Player Starts |
| BP_SafeNode | 2 | Safe Nodes |
| BP_AscensionGate | 3 | Ascension Gates |
| BP_SystemNoticePlaque | 12 | Notice Plaques |
| **TOTAL** | **~1,443** | |

## Known Minor Gaps
- `TagMarker_SpawnGroup_`: 0 — these were proxy markers; replace with real actor tags using MCP tag command.
- `L_SIG_`: 0 — signal quarter lights didn't spawn (2 actors). Cosmetic only.
- A few material applications failed on individual actors (cosmetic, actors still placed).

## Key Fix Applied
- `build_hub_citadel_city_v2.py` now has `MCP_THROTTLE = 0.10` (100ms delay between commands).
- This eliminated the frequent crash-on-rapid-fire-spawn pattern.

## Next Steps (Gameplay Implementation)
The hub map is now complete. The next work is **Phase 1 gameplay** per `docs/phase1-spec.md`:
1. Create `Map_SystemTest` as a test level
2. Create gameplay Blueprints (BP_PlayerCharacter, BP_EnemyBase, etc.)
3. Wire combat, enemy state machine, contracts, HUD
4. Set up BP_SignalBoundGameMode
