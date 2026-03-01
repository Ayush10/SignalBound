# Phase 1 Handoff — Claude Windows Continuation

**Date:** 2026-03-01
**From:** Claude Code (macOS via MCP TCP)
**To:** Claude (Windows, presumably via Unreal Editor directly)

---

## What Was Built (Complete)

### Infrastructure (Step 0)
- **C++ Game Module** (`Source/SignalBound/`) — 3 UUserWidget subclasses:
  - `SBWidget_PlayerHUD` (health bar, stamina bar, cooldown arc, skill icon)
  - `SBWidget_SystemNotice` (notice panel + text)
  - `SBWidget_SystemMenu` (tab switcher with 3 panels)
- **MCP Widget Extension** — 4 new commands added to plugin (`EpicUnrealMCPWidgetCommands.cpp/.h`):
  - `create_widget_blueprint`, `add_widget_to_canvas`, `set_widget_slot`, `set_widget_appearance`
- **CDO Fallback** added to `BPVariables.cpp` — allows setting inherited variable defaults on child BPs (REQUIRES plugin recompile to activate)

### Blueprints Created (14 total, all at `/Game/Blueprints/`)

| Blueprint | Parent | Variables | Functions | Components | Status |
|-----------|--------|-----------|-----------|------------|--------|
| BP_SafeNode | Actor | 3 (bIsActive, NodeLabel, HealAmount) | 0 | BaseMesh, GlowMesh, TriggerVolume (Sphere r=200) | Wired |
| BP_AscensionGate | Actor | 4 (bIsUnlocked, RequiredKillCount, GateLabel, DestinationMap) | 0 | GateFrameLeft, GateFrameRight, GateLintel, TriggerVolume (Box) | Wired |
| BP_SystemNoticePlaque | Actor | 2 (NoticeText, bHasBeenRead) | 0 | PlaqueMesh, TriggerVolume (Box) | Wired |
| BP_GameConfig | Actor | 12 (map names, floor configs) | 3 (GetMapNameForFloor, GetRoomCountForFloor, GetSpawnTagForFloor) | None | Data-only, no event graph needed |
| BP_EnemyBase | Character | 19 (health, combat, movement, state) | 10 (ReceiveDamage, EnterState, TickStateMachine, TickIdle..TickHitReact, Die) | DetectionSphere, AttackRangeSphere, WeaponCollision | Wired |
| BP_Enemy_Thrall | BP_EnemyBase | (inherited only) | (inherited) | (inherited) | **NEEDS OVERRIDES** |
| BP_Enemy_Skitter | BP_EnemyBase | (inherited only) | (inherited) | (inherited) | **NEEDS OVERRIDES** |
| BP_Enemy_Hexer | BP_EnemyBase | (inherited only) | (inherited) | (inherited) | **NEEDS OVERRIDES** |
| BP_Elite_Oathguard | BP_EnemyBase | (inherited only) | (inherited) | (inherited) | **NEEDS OVERRIDES + EXTRA VARS** |
| BP_PlayerCharacter | Character | 30 (health, stamina, combat, sword skill, lock-on, HUD) | 13 (TakeDamageCustom, TryLightAttack, etc.) | CameraBoom (Spring Arm), FollowCamera (Camera) | Wired |
| BP_SystemManager | Actor | ~10 (directive system) | 5 (RequestDirective, GetScriptedDirective, ShowDirective, ClearDirective, GetCurrentDirective) | None | Wired |
| BP_ContractManager | Actor | ~12 (contract tracking) | 10 (OfferContract, AcceptContract, UpdateContract, etc.) | None | Wired |
| BP_HUDManager | Actor | ~6 (widget refs) | 6 (UpdateHealth, UpdateStamina, UpdateCooldown, ShowNotice, ShowDirective, ToggleMenu) | None | Wired |
| BP_SignalBoundGameMode | GameModeBase | 0 | 0 | None | Wired |

### Event Graph Connections (Working)

```
BP_SafeNode:
  BeginPlay → Print(NodeLabel)
  ActorBeginOverlap → Branch(bIsActive) → Print("Safe Node Activated")

BP_AscensionGate:
  ActorBeginOverlap → Branch(bIsUnlocked) → Print("Gate Open")

BP_SystemNoticePlaque:
  ActorBeginOverlap → Branch(bHasBeenRead).else → Print(NoticeText) → Set(bHasBeenRead=true)

BP_EnemyBase:
  BeginPlay → Print("Enemy Spawned")
  Tick → Branch(bIsDead).else → TickStateMachine(DeltaTime)

BP_PlayerCharacter:
  BeginPlay → Print("Player Spawned")
  Tick → UpdateStaminaRegen → UpdateSwordSkillCooldown → UpdateHUDValues

BP_SystemManager:
  BeginPlay → RequestDirective → Print

BP_ContractManager:
  Tick → Branch(bContractActive) → UpdateContract

BP_HUDManager:
  BeginPlay → CreateHUD → Print

BP_SignalBoundGameMode:
  BeginPlay → Print("GameMode Initialized")
```

### Actors Spawned in Map_HubCitadelCity (17 total)

All spawned at coordinates that avoid the existing citadel city geometry:

| Actor | Location | Notes |
|-------|----------|-------|
| BP_SafeNode_01 | (-6000, 5000, 120) | Near monument hall |
| BP_SafeNode_02 | (5000, -3000, 120) | Near altar district |
| BP_SafeNode_03 | (15000, 2000, 120) | Near guardian area |
| BP_SystemNoticePlaque_01 | (-3000, 0, 120) | Central plaza |
| BP_SystemNoticePlaque_02 | (8000, -5000, 120) | Archive approach |
| BP_AscensionGate_01 | (0, 8000, 120) | Northern gate |
| BP_Enemy_Thrall_01 | (-8000, 3000, 120) | Monument patrol |
| BP_Enemy_Thrall_02 | (3000, -6000, 120) | Altar patrol |
| BP_Enemy_Skitter_01 | (-5000, -4000, 120) | Roaming |
| BP_Enemy_Skitter_02 | (10000, 3000, 120) | Guardian area |
| BP_Enemy_Hexer_01 | (6000, -8000, 120) | Archive sniper |
| BP_Elite_Oathguard_01 | (12000, 0, 120) | Gate guardian |
| BP_GameConfig_01 | (0, 0, -500) | Hidden under map |
| BP_SystemManager_01 | (0, 0, -500) | Hidden under map |
| BP_ContractManager_01 | (0, 0, -500) | Hidden under map |
| BP_HUDManager_01 | (0, 0, -500) | Hidden under map |
| BP_PlayerCharacter_01 | (-10000, 0, 200) | Player start area |

---

## What FAILED / Remains Incomplete

### 1. Child Enemy Variable Overrides (CRITICAL)

**Problem:** The MCP plugin's `set_blueprint_variable_properties` command only searches `Blueprint->NewVariables` — inherited variables from parent BPs are not found. Child BPs (Thrall, Skitter, Hexer, Oathguard) need different stat values than BP_EnemyBase defaults.

**Fix already written but not compiled:** I modified `Plugins/UnrealMCP/Source/UnrealMCP/Private/Commands/BlueprintGraph/BPVariables.cpp` to add a CDO (Class Default Object) fallback. When a variable isn't in `NewVariables`, it looks it up on the generated class CDO and uses `ImportText_Direct` to set the value.

**To activate:** Trigger Live Coding (Ctrl+Alt+F11) or restart the editor to recompile the plugin. Then run `mcp_cleanup_children.py`.

**If MCP approach still fails, set these manually in the editor Details panel:**

| Child BP | Variable Overrides |
|----------|-------------------|
| BP_Enemy_Thrall | MaxHealth=60, CurrentHealth=60, AttackDamage=12, ChaseSpeed=300, WindupDuration=1.2, RecoveryDuration=1.5, AttackRange=180 |
| BP_Enemy_Skitter | MaxHealth=30, CurrentHealth=30, AttackDamage=8, ChaseSpeed=600, WindupDuration=0.4, RecoveryDuration=0.5, AttackRange=150, StaggerThreshold=15 |
| BP_Enemy_Hexer | MaxHealth=45, CurrentHealth=45, AttackDamage=18, ChaseSpeed=250, WindupDuration=1.0, RecoveryDuration=2.0, AttackRange=800, DetectionRange=1500, bIsRanged=true |
| BP_Elite_Oathguard | MaxHealth=200, CurrentHealth=200, AttackDamage=35, ChaseSpeed=280, WindupDuration=1.5, RecoveryDuration=2.0, AttackRange=250, StaggerThreshold=60 |

### 2. Oathguard Extra Variables (FAILED)

**Problem:** `create_variable` returned "Failed to create variable" for `bHasShield` (bool) and `ShieldHealth` (float) on BP_Elite_Oathguard. Variables already existed from a prior run attempt but the error message was misleading — they may already be present, or they may be phantom entries from the broken VariableSet nodes that were later deleted.

**Fix:** Open BP_Elite_Oathguard in the editor. Check if `bHasShield` and `ShieldHealth` exist. If not, add them manually:
- `bHasShield` (bool, default: true, category: Config)
- `ShieldHealth` (float, default: 100.0, category: Config)

### 3. Broken VariableSet Nodes on Child BPs (COSMETIC)

**Problem:** Empty VariableSet nodes (no data pins, only exec pins) were created on child BPs when trying to set inherited variable values. I deleted most of them via `delete_node` but couldn't verify all were removed before the editor crashed.

**Fix:** Open each child enemy BP (Thrall, Skitter, Hexer, Oathguard). If you see orphaned "Set" nodes with no variable reference, delete them.

### 4. Node Deletion Not Fully Verified

Some orphaned/disconnected nodes may remain:
- `K2Node_IfThenElse_0` on several BPs (unused second Branch nodes from the initial build)
- Unused Tick/Overlap events on child enemy BPs
- Extra VariableGet nodes that were meant to feed into now-deleted Set nodes

**Fix:** Open each child BP, select orphaned nodes, delete.

### 5. Function Body Logic (NOT IMPLEMENTED)

All custom functions were created with I/O parameters but **no internal node graphs**. The function bodies are empty. This means:
- `ReceiveDamage`, `EnterState`, `TickStateMachine`, `TickIdle`..`TickHitReact`, `Die` — all empty
- `TakeDamageCustom`, `TryLightAttack`, `TryHeavyAttack`, `TryDodge`, `StartBlock`, `StopBlock`, etc. — all empty
- `RequestDirective`, `GetScriptedDirective`, `ShowDirective`, etc. — all empty
- `OfferContract`, `AcceptContract`, `UpdateContract`, etc. — all empty
- `GetMapNameForFloor`, `GetRoomCountForFloor`, `GetSpawnTagForFloor` — all empty

**Why:** MCP can create functions and define I/O params, but building the internal node graph of each function (the actual logic) requires many sequential add_node + connect_nodes calls per function. With 50+ functions across all BPs, this would require hundreds of MCP calls. The event graph wiring (BeginPlay, Tick chains) was prioritized.

**Fix:** Implement function bodies. The logic for each function is fully specified in `docs/phase1-spec.md`. For key functions:

**BP_EnemyBase — ReceiveDamage(DamageAmount:float):**
```
CurrentHealth -= DamageAmount
AccumulatedStagger += DamageAmount
Branch(CurrentHealth <= 0) → Die()
Branch(AccumulatedStagger >= StaggerThreshold) → EnterState(5) [Stunned], Reset AccumulatedStagger
else → EnterState(6) [HitReact]
```

**BP_EnemyBase — TickStateMachine(DeltaTime:float):**
```
SwitchOnInt(CurrentStateIndex):
  0 → TickIdle()
  1 → TickChase()
  2 → TickWindup()
  3 → TickAttack()
  4 → TickRecover()
  5 → TickStunned()
  6 → TickHitReact()
```

**BP_PlayerCharacter — TakeDamageCustom(DamageAmount:float):**
```
Branch(bIsInvincible) → return
Branch(bParryWindowActive) → OnParrySuccess(), return
Branch(bIsBlocking) → stamina drain, return
CurrentHealth -= DamageAmount
Branch(CurrentHealth <= 0) → Die()
```

See `docs/phase1-spec.md` for complete function logic specifications.

### 6. Widget Blueprints (Step 7 — NOT STARTED)

The C++ widget base classes and MCP widget extension commands were created but never used to build the actual Widget Blueprints:
- `WBP_PlayerHUD` (parent: SBWidget_PlayerHUD)
- `WBP_SystemNotice` (parent: SBWidget_SystemNotice)
- `WBP_SystemMenu` (parent: SBWidget_SystemMenu)

**Requires:** C++ module compilation first (the Source/SignalBound module). After that, use the MCP widget commands or create them in the UMG editor.

### 7. Input Binding (NOT STARTED)

BP_PlayerCharacter has no Enhanced Input bindings. Needs:
- IA_Attack (left click) → TryLightAttack
- IA_HeavyAttack (right click) → TryHeavyAttack
- IA_Dodge (space) → TryDodge
- IA_Block (shift) → StartBlock/StopBlock
- IA_SwordSkill (Q) → TrySwordSkill
- IA_LockOn (middle click) → Toggle bIsLockedOn
- IA_Menu (Tab/Esc) → ToggleMenu on HUDManager

### 8. GameMode Not Set as Default

BP_SignalBoundGameMode needs to be set as the default game mode in Project Settings → Maps & Modes.

### 9. Animation / Meshes / Materials

All actors use invisible/default meshes. No skeletal meshes, animation blueprints, or materials assigned.

---

## Key MCP API Learnings (for future sessions)

### Working Commands
```
ping
create_blueprint (name, parent_class)
add_component_to_blueprint (blueprint_name, component_name, component_type [FULL path like /Script/Engine.StaticMeshComponent])
create_variable (blueprint_name, variable_name, variable_type, default_value, category)
create_function (blueprint_name, function_name)
add_function_input / add_function_output (blueprint_name, function_name, param_name, param_type)
add_event_node (blueprint_name, event_name [e.g. "ReceiveBeginPlay", "ReceiveTick", "ReceiveActorBeginOverlap"])
add_blueprint_node (blueprint_name, node_type, node_params{})
connect_nodes (blueprint_name, source_node_id, source_pin_name, target_node_id, target_pin_name)
delete_node (blueprint_name, node_id)
compile_blueprint (blueprint_name)
analyze_blueprint_graph (blueprint_path [e.g. "/Game/Blueprints/BP_Name"])
spawn_blueprint_actor (blueprint_name, actor_name, location{x,y,z})
set_blueprint_variable_properties (blueprint_name, variable_name, default_value, category, etc.)
```

### Pin Name Conventions
- Event output exec: `"then"`
- Branch true: `"then"`, false: `"else"`, condition: `"Condition"`
- CallFunction input exec: `"execute"`, output exec: `"then"`
- PrintString input text: `"InString"`

### CallFunction for Custom BP Functions
Must include `target_class`:
```json
{
  "node_type": "CallFunction",
  "node_params": {
    "target_function": "MyFunction",
    "target_class": "/Game/Blueprints/BP_Name.BP_Name_C"
  }
}
```

### Component Types (Full Class Paths Required)
```
/Script/Engine.StaticMeshComponent
/Script/Engine.SphereComponent
/Script/Engine.BoxComponent
/Script/Engine.SpringArmComponent
/Script/Engine.CameraComponent
```

### Known Limitations
- VariableSet/VariableGet nodes can't reference inherited parent variables (pins don't materialize)
- No `remove_blueprint_node` command (use `delete_node` instead)
- `save_current_level` returns "Unknown command" despite being registered
- `spawn_actor` type whitelist doesn't include PlayerStart
- No LiteralFloat/LiteralBool node types
- No enum variable support
- Widget BP creation requires the C++ extension (standard MCP can't do it)

---

## File Inventory

### Scripts (project root)
| File | Purpose |
|------|---------|
| `mcp_cmd.py` | Simple TCP helper for one-off MCP commands |
| `mcp_build.py` | Main build script (Steps 1-9), already run |
| `mcp_fix.py` | First fix pass (CallFunction nodes, exec connections) |
| `mcp_reconnect.py` | Reconnection pass for lost exec chains |
| `mcp_final_fix.py` | Final fix (re-adds CallFunction nodes after editor restart) |
| `mcp_child_overrides.py` | Child enemy variable overrides (needs plugin recompile) |
| `mcp_cleanup_children.py` | Deletes broken VariableSet nodes + retries CDO overrides |

### C++ Files Modified/Created
| File | What |
|------|------|
| `Source/SignalBound/` | Entire game module (new) |
| `Plugins/UnrealMCP/.../EpicUnrealMCPWidgetCommands.cpp/.h` | Widget MCP commands (new) |
| `Plugins/UnrealMCP/.../BPVariables.cpp` | CDO fallback for inherited vars (modified) |
| `Plugins/UnrealMCP/.../EpicUnrealMCPBridge.cpp` | Widget command registration (modified) |
| `Plugins/UnrealMCP/UnrealMCP.Build.cs` | Added UMG/UMGEditor deps (modified) |

### Documentation
| File | What |
|------|------|
| `docs/phase1-spec.md` | Full spec for all 19 assets, function logic, variable tables |
| `docs/mcp-capabilities.md` | All 43+ MCP commands, node types, pin conventions |
| `docs/plugin-architecture.md` | Plugin C++ structure, how to add commands |
| `docs/cpp-module-spec.md` | C++ module design, widget class specs |
| `docs/phase1-handoff-claude-windows.md` | THIS FILE |

---

## Priority Order for Remaining Work

1. **Set child enemy variable overrides** (open each child BP in editor, change values in Details panel)
2. **Add Oathguard extra vars** (bHasShield, ShieldHealth) if missing
3. **Implement function bodies** — start with BP_EnemyBase (ReceiveDamage, TickStateMachine, Die) and BP_PlayerCharacter (TakeDamageCustom, TryLightAttack, TryDodge)
4. **Set BP_SignalBoundGameMode as default**
5. **Compile C++ module** (Source/SignalBound) and create Widget Blueprints
6. **Wire up Enhanced Input** on BP_PlayerCharacter
7. **Clean up orphaned nodes** on child BPs
