#!/usr/bin/env python3
"""Clean all non-entry nodes from blueprint function graphs and EventGraph."""

from __future__ import annotations
import sys
import time
from typing import Any, Dict, List

from mcp_path import resolve_mcp_py_dir

MCP_PY_DIR = resolve_mcp_py_dir()
if str(MCP_PY_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_PY_DIR))

import unreal_mcp_server_advanced as server  # type: ignore

unreal = server.get_unreal_connection()


def send(cmd: str, params: Dict[str, Any]) -> Dict[str, Any]:
    time.sleep(0.1)
    return unreal.send_command(cmd, params) or {}


def clean_function_graph(bp_name: str, bp_path: str, func_name: str) -> int:
    resp = send("analyze_blueprint_graph", {"blueprint_path": bp_path, "graph_name": func_name})
    nodes = resp.get("result", {}).get("graph_data", {}).get("nodes", [])
    deleted = 0
    for n in nodes:
        name = n.get("name", "")
        if "FunctionEntry" in name:
            continue
        r = send("delete_node", {"blueprint_name": bp_name, "node_id": name, "function_name": func_name})
        if r.get("status") != "error":
            deleted += 1
    return deleted


def clean_event_graph(bp_name: str, bp_path: str) -> int:
    resp = send("analyze_blueprint_graph", {"blueprint_path": bp_path, "graph_name": "EventGraph"})
    nodes = resp.get("result", {}).get("graph_data", {}).get("nodes", [])
    deleted = 0
    for n in nodes:
        name = n.get("name", "")
        r = send("delete_node", {"blueprint_name": bp_name, "node_id": name})
        if r.get("status") != "error":
            deleted += 1
    return deleted


def clean_blueprint(bp_name: str, functions: List[str]) -> None:
    bp_path = f"/Game/Blueprints/{bp_name}"
    print(f"\n=== Cleaning {bp_name} ===")

    total = 0
    for fn in functions:
        d = clean_function_graph(bp_name, bp_path, fn)
        print(f"  {fn}: deleted {d} nodes")
        total += d

    d = clean_event_graph(bp_name, bp_path)
    print(f"  EventGraph: deleted {d} nodes")
    total += d

    print(f"  Total: {total} nodes deleted")


if __name__ == "__main__":
    ping = send("ping", {})
    if ping.get("status") == "error":
        print(f"MCP not available: {ping}")
        raise SystemExit(2)

    # Clean BP_PlayerCharacter
    clean_blueprint("BP_PlayerCharacter", [
        "TakeDamageCustom", "TryLightAttack", "TryHeavyAttack", "TryDodge",
        "StartBlock", "StopBlock", "TrySwordSkill", "OnParrySuccess", "Die",
        "UpdateStaminaRegen", "UpdateSwordSkillCooldown", "UpdateHUDValues", "ResetAttackState",
    ])

    # Clean BP_EnemyBase
    clean_blueprint("BP_EnemyBase", [
        "ReceiveDamage", "EnterState", "TickStateMachine", "TickIdle", "TickChase",
        "TickWindup", "TickAttack", "TickRecover", "TickStunned", "TickHitReact", "Die",
    ])

    # Clean system/contract/gamemode/markers
    clean_blueprint("BP_SystemManager", [
        "RequestDirective", "GetScriptedDirective", "ShowDirective", "ClearDirective", "GetCurrentDirective",
    ])
    clean_blueprint("BP_ContractManager", [
        "OfferContract", "AcceptContract", "UpdateContract", "ContractSuccess", "ContractFail",
        "OnPlayerDamaged", "OnPlayerParried", "OnEnemyKilled", "OnPlayerHealed", "GetContractDescription",
    ])
    clean_blueprint("BP_SignalBoundGameMode", [])
    clean_blueprint("BP_HUDManager", [
        "CreateHUD", "UpdateHealth", "UpdateStamina", "UpdateCooldown",
        "ShowNotice", "ShowDirective", "ToggleMenu",
    ])
    clean_blueprint("BP_SafeNode", [])
    clean_blueprint("BP_AscensionGate", [])
    clean_blueprint("BP_SystemNoticePlaque", [])

    print("\nDONE: All blueprints cleaned.")
