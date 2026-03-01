# SignalBound

A third-person melee action game built in Unreal Engine 5.7. Players navigate procedurally-guided dungeon floors, complete contracts for an omniscient AI overseer called the System, and ascend through a citadel hub city. Combat is stamina-based with light/heavy attacks, dodge rolls, parry windows, and cooldown-gated sword skills.

## Repository Structure

```
SignalBound.uproject          # UE 5.7 project file
Source/SignalBound/            # C++ gameplay module (15 classes)
  Public/Gameplay/             #   Player, enemies, managers, objectives
  Public/UI/                   #   HUD, System notice, System menu widgets
  Private/Gameplay/            #   Implementations
  Private/UI/                  #   Widget implementations
Plugins/UnrealMCP/             # Extended MCP plugin for editor automation
Content/Blueprints/            # 16 Blueprint assets
Config/                        # Engine, editor, input config
tools/                         # MCP helper scripts and automation
docs/                          # Specs, architecture, handoff notes
```

## Maps

| Map | Purpose | Status |
|-----|---------|--------|
| Map_SystemTest | Graybox test level for PIE smoke tests | Created, player start placed |
| Map_HubCitadelCity | Citadel hub city with ~1,443 actors | Complete, all markers placed |
| Map_Floor01_Ironcatacomb | First dungeon floor with 3 combat rooms | Environment complete, markers placed |

## C++ Gameplay Module

15 classes across combat, AI, systems, UI, and level objectives:

**Combat**
- `ASBPlayerCharacter` — Light attack combos, heavy attack, dodge with i-frames, block/parry, sword skill on cooldown, stamina system
- `ASBEnemyBase` — 8-state AI machine (Idle/Chase/Windup/Attack/Recover/Stunned/HitReact/Dead), NavMesh pathfinding, stagger system

**Systems**
- `ASBSystemManager` — 3 provider modes (Scripted/Cached/LiveStub), directive history, fallback behavior
- `ASBContractManager` — 6 contract types (NoHeal, ParryChain, NoHits, KillCount, LowHPSurvival, FastClear), offer/accept/track/complete/fail flow

**UI**
- `ASBHUDManager` — Creates and binds PlayerHUD, SystemNotice, SystemMenu widgets
- `USBWidget_PlayerHUD` — Health/stamina bars, cooldown arc, contract/directive text
- `USBWidget_SystemNotice` — Fade-in/out directive display with auto-hide timer
- `USBWidget_SystemMenu` — 3-tab overlay (Status/Contracts/Skills) with input mode switching

**Level Flow**
- `ASBSignalBoundGameMode` — Spawns and binds all managers, connects HUD to player delegates
- `ASBFloor01ObjectiveManager` — Lever/sigil tracking, boss gate evaluation, ascension trigger
- `ASBLevelTransitionTrigger` — Overlap-based level transition with optional OpenLevel
- `ASBObjectiveLever`, `ASBBossGate`, `ASBEnemySpawnMarker` — World interaction actors

**Types**
- `SBGameplayTypes.h` — Enums (ESBEnemyState, ESBSystemProviderMode, ESBContractType) and structs (FSBSystemDirective, FSBContractState)

## Blueprints

16 Blueprint assets in `Content/Blueprints/`:
- Core: BP_PlayerCharacter, BP_EnemyBase, BP_SystemManager, BP_ContractManager, BP_SignalBoundGameMode, BP_HUDManager
- Enemies: BP_Enemy_Thrall, BP_Enemy_Skitter, BP_Enemy_Hexer, BP_Elite_Oathguard
- World: BP_SafeNode, BP_AscensionGate, BP_SystemNoticePlaque, BP_GameConfig, BP_Floor01ObjectiveManager

Blueprints are scaffolded with variables and function stubs. They need to be reparented to their C++ counterparts after compilation.

## MCP Plugin Extensions

The `UnrealMCP` plugin has been extended with:
- Actor tags, labels, light properties, text render components
- Map save/load/new level commands
- Enhanced actor filtering (by type, name pattern, max results)
- Self-call support for Blueprint function nodes
- Crash guards against material mutation during save/GC
- 100ms throttle convention to prevent rapid-fire crashes

## Current Progress

| Phase | Status |
|-------|--------|
| 0 — Project setup | Partially complete (C++ not yet compiled) |
| 1 — Combat vertical slice | Partially complete (code written, untested) |
| 2 — System foundation | Partially complete (providers work, no record/replay) |
| 3 — Contracts and UI | Partially complete (logic done, no widget assets) |
| 4 — Hub city | Complete |
| 5 — Floor 1 | Partially complete (environment done, navmesh untested) |
| 6 — Gameplay loop | Not started |
| 7 — Mistral/ElevenLabs | Not started |
| 8 — Polish and demo | Not started |

**Critical blocker:** The C++ module has never been compiled into running DLLs. The build sequence is: close editor, run UBT build, reopen editor, reparent BPs to C++ classes, then PIE test.

## Setup

### Prerequisites
- Unreal Engine 5.7
- Python 3.13 + `uv`
- `unreal-engine-mcp` Python server repo cloned locally

### Steps
1. Install Unreal Engine 5.7.
2. Open `SignalBound.uproject` once so Unreal builds project/plugin binaries.
3. Clone `unreal-engine-mcp` (the Python MCP server repo) somewhere on disk.
4. Set environment variable `UNREAL_MCP_PY_DIR` to `<path>/unreal-engine-mcp/Python`.
5. Restart Unreal Editor after any `Plugins/UnrealMCP` C++ changes.

### Windows Notes
- Helper scripts are path-portable through `UNREAL_MCP_PY_DIR`.
- Use PowerShell wrapper: `tools/unreal_mcp_exec.ps1 ping '{}'`
- If Unreal shows old MCP command behavior, close editor, reopen project, and let the plugin recompile.

### Building the C++ Module
```
# Close Unreal Editor first, then:
# Windows (from UE install dir):
Engine\Build\BatchFiles\Build.bat SignalBoundEditor Win64 Development "<path>/SignalBound.uproject"

# macOS:
Engine/Build/BatchFiles/Mac/Build.sh SignalBoundEditor Mac Development "<path>/SignalBound.uproject"
```

## MCP Helper Commands

```bash
# Ping MCP server
tools/unreal_mcp_exec.sh ping '{}'

# Find actor by name
tools/unreal_mcp_exec.sh find_actors_by_name '{"pattern":"BP_SafeNode_00"}'

# Run hub builder phase
uv --directory "$UNREAL_MCP_PY_DIR" run python tools/build_signalbound_hub.py --phase markers

# Lighting pass
uv --directory "$UNREAL_MCP_PY_DIR" run python tools/fix_hub_lighting.py
```

## Key Documentation

| Document | Purpose |
|----------|---------|
| `docs/phase1-spec.md` | Full Phase 1 spec — blueprints, variables, functions, naming |
| `docs/cpp-module-spec.md` | C++ module structure and class details |
| `docs/mcp-capabilities.md` | All 43 MCP tools, node types, pin conventions |
| `docs/plugin-architecture.md` | Plugin structure, how to add commands |
| `docs/MAJOR_CHANGES.md` | Chronological log of significant changes |
| `docs/STATUS_REPORT_PHASE1_PROGRESS_2026-03-01.md` | Detailed Phase 1 progress report |
| `docs/ENV_COMPLETION_REPORT_2026-03-01.md` | Map and environment completion status |
| `CLAUDE.md` | Project execution conventions for AI agents |

## Multi-Agent Workflow

| Agent | Responsibility |
|-------|---------------|
| Claude Code | Gameplay, combat, enemies, NPCs, contracts, System directives, UI |
| Codex | City layout, lighting, environments |
| Gemini | Audit and review |

Sync policy: `docs/CROSS_AGENT_SYNC_POLICY.md`. Handoff notes in `docs/SESSION_HANDOFF_*.md` and `docs/WINDOWS_HANDOFF_*.md`.
