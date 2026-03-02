# SignalBound 2-Minute Demo Script (Record-Ready)

## Pre-Flight (2 minutes before recording)
1. Open `Map_HubCitadelCity`.
2. Set `BP_SystemManager.ProviderMode` to `CachedProvider` for maximum stability.
3. If you want live AI+voice, run `python tools/system_service.py` and set `LiveStub` instead.
4. Start recording at 1080p/60fps.

## Timeline (120 seconds)

### 0:00 - 0:12 (Hub Establishing)
1. Start near `BP_PlayerStart_Map_HubCitadelCity`.
2. Slow pan toward the plaza and ascension gallery.
3. Keep `BP_SystemNoticePlaque_*` and cyan system accents in frame.

Voice line:
`"SignalBound places you inside a living citadel governed by the System."`

### 0:12 - 0:28 (System + Gate Setup)
1. Walk toward `BP_AscensionGate_00`.
2. Pause 2 seconds at `BP_LevelTransition_Gate01` so the trigger area is obvious.
3. Trigger transition to Floor 1.

Voice line:
`"The hub transitions directly into challenge floors through named world triggers."`

### 0:28 - 0:42 (Floor 1 Arrival)
1. In `Map_Floor01_Ironcatacomb`, show `BP_SafeNode_01`.
2. Move into Room 1 and frame enemy spawn area.

Voice line:
`"Floor 1 is a fully navigable combat space with objective and boss progression."`

### 0:42 - 1:22 (Combat Showcase)
1. Fight 4-5 enemies in Room 1 and Room 2 path.
2. Show this sequence clearly:
   - Light combo
   - Dodge (stamina drain visible)
   - Heavy finisher
   - One parry/block moment
3. Keep HUD bars visible during action.

Voice line:
`"Combat runs on C++ state logic with stamina, hit reactions, and clean readability."`

### 1:22 - 1:46 (Objective Chain)
1. Move to Room 3 Sigil Vault.
2. Activate `BP_ObjectiveLever_01_A` and `BP_ObjectiveLever_01_B`.
3. Show boss gate side (`BP_BossGate_01`) opening state or unlocked state.

Voice line:
`"Progression is world-driven: levers, sigil sockets, and gate unlock flow."`

### 1:46 - 2:00 (Climax Frame)
1. End at boss hall/arena entrance facing `BP_BossGate_01` or boss arena.
2. Hold a hero frame for 3-4 seconds.

Voice line:
`"SignalBound combines cinematic worldbuilding, systemic progression, and combat-ready gameplay."`

## Editing Fallbacks (if load times interrupt flow)
1. Cut hub transition load screen with a hard cut at 0:28.
2. If combat takes too long, trim to 30 seconds but keep one light combo, one dodge, one heavy.
3. If gate state does not update live on camera, cut from lever pull directly to open gate shot.

## Submission Assets
1. Video: 2:00 runtime.
2. Cover image: use `HighResShot 2` from:
   - `CoverCam_Hub_GrandHall` in `Map_HubCitadelCity`
   - `DemoCam_F1_BossGateHall` in `Map_Floor01_Ironcatacomb`
