# Windows Handoff - Hub Additive Build (2026-03-01)

## Objective
Continue building `Map_HubCitadelCity` iteratively without deleting existing content.

## What Was Completed
1. Enforced additive-safe behavior in map scripts:
   - `tools/build_hub_citadel_city_v2.py`
   - `tools/build_signalbound_hub.py`
   - `tools/beautify_hub_vibrant.py`
2. Added safeguards:
   - destructive clear requires `--allow-clear`
   - replacement behavior requires `--overwrite-existing`
   - existing actors are now skipped by default (no delete/replace)
3. Restored core base hub districts from previous pass:
   - `SM_GMH_`, `SM_SD_`, `SM_AA_`, `SM_AG_`, `SM_EXT_`, `SM_VISTA_`
4. Ran additive metropolis v2 phases successfully:
   - `core`
   - `contract_vista`
   - `signal_quarter`

## What Failed / Was Interrupted
1. Phase chain was interrupted mid-run due Unreal instability (port ownership shifted to CrashReportClient once).
2. Remaining v2 phases were not completed:
   - `skyline`
   - `vehicles`
   - `arenas_outskirts`
   - `undercroft`
   - `markers_plaques`
3. Beautification flowers were not restored yet after the interrupted rebuild:
   - `SM_GARDEN_`, `SM_FLOWER_`, `SM_Rose_`, `L_BEAUTY_` currently absent.

## Current Snapshot (via MCP prefix counts)
- `SM_GMH_` = 56
- `SM_SD_` = 20
- `SM_AA_` = 42
- `SM_AG_` = 36
- `SM_EXT_` = 140
- `SM_VISTA_` = 42
- `SM_CORE_` = 225
- `SM_SIG_` = 27
- `SM_CON_` = 68
- `SM_SKY_` = 0
- `SM_TRN_` = 0
- `SM_ARENA_` = 0
- `SM_OUT_` = 0
- `SM_UND_` = 0
- `SM_VEH_` = 0
- `BP_PlayerStart_Map_HubCitadelCity` = 1
- `BP_SafeNode_00` = 1
- `BP_AscensionGate_00` = 1
- `BP_AscensionGate_01` = 1
- `BP_AscensionGate_02` = 1
- `BP_SystemNoticePlaque_` = 5
- `TagMarker_SpawnGroup_` = 10

## Exact Next Steps (Windows Codex)
1. Open `SignalBound.uproject` and wait until Unreal MCP is responsive.
2. Verify MCP:
   - `python mcp_cmd.py ping "{}"`
3. Confirm hub map context:
   - `python mcp_cmd.py find_actors_by_name "{\"pattern\":\"SM_GMH_\"}"`
4. Run remaining v2 phases (additive, no clear):
   - `python tools/build_hub_citadel_city_v2.py --phase skyline`
   - `python tools/build_hub_citadel_city_v2.py --phase vehicles`
   - `python tools/build_hub_citadel_city_v2.py --phase arenas_outskirts`
   - `python tools/build_hub_citadel_city_v2.py --phase undercroft`
   - `python tools/build_hub_citadel_city_v2.py --phase markers_plaques`
5. Restore vibrant flora additively (no refresh delete):
   - `python tools/beautify_hub_vibrant.py`
6. Save map and update this handoff with post-run counts.

## Important Note
If MCP unexpectedly fails and port `55557` is owned by `CrashReportClient`, Unreal likely crashed. Close crash reporter, reopen `SignalBound.uproject`, and rerun from step 2.

