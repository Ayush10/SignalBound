# SignalBound Phase 1: Gameplay Foundation Spec

## Project Rules
- **Map naming:** Map_SystemTest, Map_HubCitadelCity, Map_Floor01_Ironcatacomb, Map_Floor02_VerdantRuins, Map_Floor03_Skyforge
- **Actor naming:** BP_PlayerStart_{MapName}, BP_SafeNode_{FloorNumber}, BP_SystemNoticePlaque_{Index}, BP_EnemySpawn_{Floor}_{Room}_{Index}, BP_EliteSpawn_{Floor}_{Room}, BP_BossSpawn_{Floor}, BP_ObjectiveLever_{Floor}_{A/B}, BP_BossGate_{Floor}, BP_AscensionGate_{Floor}, BP_SigilSocket_{Floor}_{Index}
- **Tag convention:** SpawnGroup_HubAmbient, SpawnGroup_Floor{01-03}_Room{1-3}
- **Do NOT change names after creation.** Gameplay logic binds to them.

## Responsibility Split
- **Claude Code:** Phase 1 gameplay, combat, enemies, NPCs, contracts, System directives, UI
- **Codex:** City layout, lighting, environments. Gets marker BPs to place.

## All Blueprints to Create

### Marker Blueprints (for Codex)
| Blueprint | Parent | Components | Variables |
|---|---|---|---|
| BP_SafeNode | Actor | BaseMesh(Cylinder), GlowMesh(Sphere), TriggerVolume(Sphere,r=200) | bIsActive(bool), NodeLabel(string), HealAmount(float) |
| BP_AscensionGate | Actor | GateFrameLeft(Cube), GateFrameRight(Cube), GateLintel(Cube), TriggerVolume(Box) | bIsUnlocked(bool), RequiredKillCount(int), GateLabel(string), DestinationMap(string) |
| BP_SystemNoticePlaque | Actor | PlaqueMesh(Cube), TriggerVolume(Box) | NoticeText(string), bHasBeenRead(bool) |

### Core Gameplay Blueprints
| Blueprint | Parent | Key Systems |
|---|---|---|
| BP_PlayerCharacter | Character | 3-hit combo, heavy, dodge(stamina), block/parry, sword skill(cooldown), health/stamina |
| BP_EnemyBase | Character | State machine (8 states), detection, telegraph, damage, stagger |
| BP_Enemy_Thrall | BP_EnemyBase | Slow melee, easy parry (WindupDuration=1.2) |
| BP_Enemy_Skitter | BP_EnemyBase | Fast low HP (ChaseSpeed=600, MaxHealth=30) |
| BP_Enemy_Hexer | BP_EnemyBase | Ranged caster (AttackRange=800, bIsRanged=true) |
| BP_Elite_Oathguard | BP_EnemyBase | Shield+heavy (MaxHealth=200, bHasShield=true) |
| BP_SystemManager | Actor | Directive providers (Scripted/Cached/Live stub) |
| BP_ContractManager | Actor | 6 contract types, offer/accept/track/success/fail |
| BP_GameConfig | Actor | Map names, floor defs, spawn tags |
| BP_HUDManager | Actor | Widget spawning, data bridge |
| BP_SignalBoundGameMode | GameModeBase | Spawns all systems |

### Widget Blueprints (via C++ extension)
| Widget | C++ Parent | Contents |
|---|---|---|
| WBP_PlayerHUD | SBWidget_PlayerHUD | HealthBar(ProgressBar), StaminaBar(ProgressBar), CooldownArc(Image), ContractText(TextBlock) |
| WBP_SystemNotice | SBWidget_SystemNotice | NoticePanel(Border), NoticeText(TextBlock) |
| WBP_SystemMenu | SBWidget_SystemMenu | TabButtons(3x Button), TabSwitcher(WidgetSwitcher), 3 panels |

## Enemy State Machine (int-based)
```
0=Idle → detect player → 1=Chase → in range → 2=Windup → timer → 3=Attack → 4=Recover → 0/1
                                                    ↑ damage → 6=HitReact → 1
                                                    ↑ stagger threshold → 5=Stunned → 0
                                                    ↑ health <= 0 → 7=Dead
```

## Contract Types
| Index | Name | Condition | Target |
|---|---|---|---|
| 0 | NoHeal | Don't heal for 30s | Timer 30.0 |
| 1 | ParryChain | Land 3 parries in 25s | Count 3, Timer 25.0 |
| 2 | NoHits | Take no hits for 20s | Timer 20.0 |
| 3 | KillCount | Kill N enemies under time | Count varies |
| 4 | LowHPSurvival | Survive at <30% HP for 15s | Timer 15.0 |
| 5 | FastClear | Clear room in under N seconds | Timer varies |

## Player Combat Functions
`TakeDamageCustom`, `TryLightAttack`, `TryHeavyAttack`, `TryDodge`, `StartBlock`, `StopBlock`, `TrySwordSkill`, `OnParrySuccess`, `Die`, `UpdateStaminaRegen`, `UpdateSwordSkillCooldown`, `UpdateHUDValues`, `ResetAttackState`

## Known Gaps (Manual After MCP)
1. Enhanced Input IA_ bindings (can't reference asset objects via MCP)
2. Skeletal mesh + Animation Blueprint assignment
3. Animation montage assignments
4. Materials (placeholders used)
5. NavMesh bounds volumes
6. Weapon collision channel setup

## Testing (Map_SystemTest)
1. Set BP_SignalBoundGameMode as game mode
2. Set BP_PlayerCharacter as default pawn
3. Place: 1x Thrall, 1x Skitter, 1x SafeNode, 1x NoticePlaque
4. PIE → verify Print messages for all combat actions + enemy states
