# SignalBound — Claude Code Project Instructions

## Project Type
Unreal Engine 5.7 game project with C++ module + Blueprint gameplay systems.
MCP plugin (UnrealMCP) enables remote Blueprint creation via TCP.

## Before Starting Work
1. Read `docs/` folder for all research and specs — DO NOT re-research what's already documented
2. Check `docs/phase1-spec.md` for naming conventions and blueprint specs
3. Check Claude memory `phase1-progress.md` for current implementation step
4. Ensure Unreal Editor is running with UnrealMCP plugin enabled (port 55557)

## Key Documentation
- `docs/mcp-capabilities.md` — All 43 MCP tools, node types, pin conventions, limitations
- `docs/plugin-architecture.md` — Plugin structure, how to add commands, build deps
- `docs/phase1-spec.md` — Full Phase 1 spec (all blueprints, variables, functions, naming)
- `docs/cpp-module-spec.md` — C++ module structure, widget classes, MCP extension plan

## Naming Rules (NEVER CHANGE)
- Maps: Map_SystemTest, Map_HubCitadelCity, Map_Floor01_Ironcatacomb, Map_Floor02_VerdantRuins, Map_Floor03_Skyforge
- Actors: BP_PlayerStart_{Map}, BP_SafeNode_{Floor}, BP_EnemySpawn_{Floor}_{Room}_{Index}, etc.
- Tags: SpawnGroup_HubAmbient, SpawnGroup_Floor{01-03}_Room{1-3}
- Gameplay logic binds to these names. Changing them breaks everything.

## Responsibility Split
- **Claude Code:** Gameplay, combat, enemies, NPCs, contracts, System directives, UI scaffolding
- **Codex:** City layout, lighting, environments (places marker BPs we create)

## MCP Connection
- TCP port: 55557 (localhost)
- Plugin must be enabled in editor: Edit → Plugins → UnrealMCP → Enable
- Python server config: `~/.claude/.mcp.json`
- Test connection: `lsof -i :55557` should show UnrealEditor

## Research Saving Policy
When doing significant research (exploring APIs, reading plugin code, understanding UE systems):
1. Save findings to `docs/` as markdown files
2. Update Claude memory with summary + pointer to doc
3. Never re-research what's already in docs/

## Major Implementation Change Policy
When shipping any major code/content/system change:
1. Update `docs/MAJOR_CHANGES.md` with what changed and why
2. Create or update a dated handoff note (for example `docs/SESSION_HANDOFF_YYYY-MM-DD.md`)
3. Include exact restart steps if editor/plugin/server reload is required

## Cross-Platform Continuity
All docs/ files are git-tracked. When pushing to GitHub and cloning on Windows:
- The `docs/` folder has all specs and research needed to continue
- The `CLAUDE.md` file (this file) provides entry instructions
- Phase progress is tracked in docs and Claude memory
- MCP setup on Windows: same plugin, adjust Python path in MCP config
