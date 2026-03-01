# SignalBound Status Report - Crash Triage + Phase 1 Backbone

Date: 2026-03-01

## Summary

Two distinct crash classes were identified:

1. GPU present path crash (repeating):
- Signature: `NvPresent64.dll` + `UnrealEditor-D3D12RHI.dll`
- Error: `EXCEPTION_ACCESS_VIOLATION reading address 0x0000000000000000`
- Seen in multiple crash contexts under `Saved/Crashes/UECC-Windows-*`.

2. Plugin-side deterministic crash:
- Signature: `Illegal call to StaticFindObjectFast() while serializing object data!`
- Trigger path: `FEpicUnrealMCPBlueprintCommands::HandleApplyMaterialToActor()`
- Evidence: `Saved/Logs/SignalBound-backup-2026.03.01-18.10.16.log` callstack points to `EpicUnrealMCPBlueprintCommands.cpp` line in apply-material command during package save/autosave.

## External Corroboration (Epic + Community)

- Epic official GPU crash debugging guidance:
  - Use latest GPU drivers.
  - Use `-gpucrashdebugging` / `-d3ddebug` (separately).
  - A/B DX12 vs DX11 for isolation.
  - Source:
    - https://dev.epicgames.com/documentation/en-us/unreal-engine/dealing-with-a-gpu-crash-when-using-unreal-engine
    - https://dev.epicgames.com/documentation/en-us/unreal-engine/how-to-fix-a-gpu-driver-crash-when-using-unreal-engine?application_version=5.3

- Epic forum threads with matching `NvPresent64` stack:
  - https://forums.unrealengine.com/t/unreal-engine-crash-every-time-im-opening-second-window/2692195
  - https://forums.unrealengine.com/t/unreal-engine-5-7-and-5-6-ui-heavily-glitching-and-crashing/2696613
  - https://forums.unrealengine.com/t/opening-blueprint-crashes-unreal-engine/2656203
  - https://forums.unrealengine.com/t/unreal-engine-crashing/2660250

- Reported fixes from community threads:
  - Disable NVIDIA App Smooth Motion.
  - Disable HAGS on affected systems.
  - Disable overlays (NVIDIA/Discord) on affected systems.

## Implemented Crash Hardening

1. Plugin guard against unsafe mutation window
- File: `Plugins/UnrealMCP/Source/UnrealMCP/Private/Commands/EpicUnrealMCPBlueprintCommands.cpp`
- Added an editor safety check (`IsGarbageCollecting()` / `GIsSavingPackage`) before material mutation paths:
  - `HandleSetMeshMaterialColor`
  - `HandleApplyMaterialToActor`
  - `HandleApplyMaterialToBlueprint`
- Behavior now: returns explicit retry error instead of mutating during save/GC.

2. Renderer/editor stability defaults
- File: `Config/DefaultEngine.ini`
  - Added `r.GraphicsAdapter=0` in renderer settings and console variables.
  - Increased `r.Shadow.Virtual.MaxPhysicalPages=8192` (also addresses VSM overflow warnings observed in logs).
- File: `Config/DefaultEditor.ini`
  - Added `bAutoSaveEnable=False` to reduce autosave collisions during heavy MCP edits.

## Phase 1/2 C++ Backbone Implemented

New gameplay classes were added so implementation can continue even when BP graph editing is unstable.

### Core Types
- `Source/SignalBound/Public/Gameplay/SBGameplayTypes.h`
  - `ESBEnemyState`, `ESBSystemProviderMode`, `ESBContractType`
  - `FSBSystemDirective`, `FSBContractState`

### Player Combat
- `ASBPlayerCharacter`
  - Files:
    - `Source/SignalBound/Public/Gameplay/SBPlayerCharacter.h`
    - `Source/SignalBound/Private/Gameplay/SBPlayerCharacter.cpp`
  - Implemented functions:
    - `TakeDamageCustom`
    - `TryLightAttack`, `TryHeavyAttack`
    - `TryDodge`
    - `StartBlock`, `StopBlock`, `OnParrySuccess`
    - `TrySwordSkill`
    - `Die`
    - `UpdateStaminaRegen`, `UpdateSwordSkillCooldown`, `UpdateHUDValues`, `ResetAttackState`
  - Exposes delegate outputs for HUD binding.

### Enemy State Machine
- `ASBEnemyBase`
  - Files:
    - `Source/SignalBound/Public/Gameplay/SBEnemyBase.h`
    - `Source/SignalBound/Private/Gameplay/SBEnemyBase.cpp`
  - Implemented state loop:
    - `ReceiveDamage`, `EnterState`, `TickStateMachine`
    - `TickIdle`, `TickChase`, `TickWindup`, `TickAttack`, `TickRecover`, `TickStunned`, `TickHitReact`
    - `Die`, `PerformAttack`
  - Includes AI-controller MoveTo fallback + movement input fallback.

### System + Contracts
- `ASBSystemManager`
  - Files:
    - `Source/SignalBound/Public/Gameplay/SBSystemManager.h`
    - `Source/SignalBound/Private/Gameplay/SBSystemManager.cpp`
  - Scripted/cached/live-stub provider behavior + directive history.

- `ASBContractManager`
  - Files:
    - `Source/SignalBound/Public/Gameplay/SBContractManager.h`
    - `Source/SignalBound/Private/Gameplay/SBContractManager.cpp`
  - Offer/accept/update/fail/complete with counters for parry/kill/no-hit style objectives.

### HUD + GameMode + Objectives
- `ASBHUDManager`
  - Creates and updates `SBWidget_PlayerHUD`, `SBWidget_SystemNotice`, `SBWidget_SystemMenu`.
- `ASBSignalBoundGameMode`
  - Spawns/fetches `SystemManager`, `ContractManager`, `HUDManager`.
- `ASBLevelTransitionTrigger`
  - Transition overlap trigger with optional `OpenLevel`.
- `ASBObjectiveLever`
  - Lever activation state + event.
- `ASBBossGate`
  - Gate open condition by lever/sigil counts.
- `ASBEnemySpawnMarker`
  - Spawn metadata actor for group/floor/room tagging.

## Build / Validation Status

- C++ compile reached link stage successfully.
- Build link failed only because `UnrealEditor.exe` had module DLLs locked (expected when editor is open during full external build).
- Live coding trigger was sent (`Ctrl+Alt+F11`) from `tools/trigger_live_coding.ps1`.

## Test Plan (Immediate)

1. Close editor, then run full build:
- `Build.bat SignalBoundEditor Win64 Development <uproject>`

2. Reopen editor and verify plugin command safety:
- Issue repeated `apply_material_to_actor` during map save/autosave.
- Expected: retry error during unsafe window, no crash.

3. Verify player/enemy code path in `Map_SystemTest`:
- Reparent or create BP children from `ASBPlayerCharacter` / `ASBEnemyBase`.
- Confirm combat functions execute and enemy transitions run.

4. Verify managers:
- Set game mode to `ASBSignalBoundGameMode` or BP child.
- Confirm system directives and contract updates broadcast.

5. Verify transition/objective wiring:
- Place `ASBLevelTransitionTrigger`, `ASBObjectiveLever`, `ASBBossGate`.
- Confirm overlap events and gate state progression.

## Next Integration Step

Bind existing `BP_*` assets to these C++ classes (or reparent safely) to complete the task list without deleting existing world objects.
