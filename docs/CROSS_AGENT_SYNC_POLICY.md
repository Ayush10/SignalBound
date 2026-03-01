# Cross-Agent Sync Policy (Claude + Codex)

Date: 2026-03-01

## Goal
Keep Claude Code and Codex workstreams aligned so environment/map/code changes do not conflict.

## Required Cadence
- Run a sync check at least every 5 minutes during active work.
- Run a sync check immediately before:
  - any phase runner script
  - any map clear/delete command
  - any Git push

## Sync Check Commands
1. `git status --short`
2. `git log --oneline -n 5`
3. Review newest handoff/status docs in `docs/`:
   - `SESSION_HANDOFF_*.md`
   - `WINDOWS_HANDOFF_*.md`
   - `MAP_HUB_PROGRESS_*.md`

## MCP/Editor Verification
Before map automation:
1. `python3 mcp_cmd.py ping '{}'`
2. Confirm current hub anchors exist:
   - `SM_GMH_` prefix actors > 0
   - `BP_PlayerStart_Map_HubCitadelCity` exists

## Safety Rules
- Default mode is additive only.
- Never run destructive map cleanup unless both are true:
  1. user explicitly asked for cleanup
  2. `--allow-clear` flag is used
- Never replace existing actors unless required:
  - use `--overwrite-existing` only when intentional

## Handoff Minimum Content
Every major pass must record:
1. What was completed
2. What failed or was interrupted
3. Current actor snapshot (key prefixes)
4. Exact next commands for continuation (macOS + Windows where applicable)

