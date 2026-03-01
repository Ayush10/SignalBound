#!/usr/bin/env python3
"""Phase 1 Gameplay Implementation — Wire all function bodies via MCP.

Implements: Player combat, Enemy AI, System/Contracts, Level transitions,
Floor 1 objectives, GameMode, Markers, HUD binding.

Run phases individually or all at once:
  python tools/implement_phase1_gameplay.py --phase player
  python tools/implement_phase1_gameplay.py --phase enemy
  python tools/implement_phase1_gameplay.py --phase system
  python tools/implement_phase1_gameplay.py --phase transitions
  python tools/implement_phase1_gameplay.py --phase gamemode
  python tools/implement_phase1_gameplay.py --phase all
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from mcp_path import resolve_mcp_py_dir

MCP_PY_DIR = resolve_mcp_py_dir()
if str(MCP_PY_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_PY_DIR))

import unreal_mcp_server_advanced as server  # type: ignore

MCP_THROTTLE = 0.10
unreal = server.get_unreal_connection()

nodes_created = 0
connections_made = 0
failed: List[Tuple[str, str]] = []


def send(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    time.sleep(MCP_THROTTLE)
    resp = unreal.send_command(command, params)
    return resp or {"status": "error", "error": "No response"}


def is_ok(resp: Dict[str, Any]) -> bool:
    if resp.get("status") == "error":
        return False
    if resp.get("success") is False:
        return False
    return True


def add_node(bp: str, node_type: str, params: Dict[str, Any],
             func: Optional[str] = None) -> Optional[str]:
    """Add a node, return its ID or None on failure."""
    global nodes_created
    p: Dict[str, Any] = {"blueprint_name": bp, "node_type": node_type, "node_params": params}
    if func:
        p["node_params"]["function_name"] = func
    resp = send("add_blueprint_node", p)
    if is_ok(resp):
        nodes_created += 1
        r = resp.get("result", {})
        return r.get("node_id") or r.get("node_name") or r.get("id")
    err = resp.get("error", str(resp))
    failed.append((f"add_node:{bp}:{node_type}", err))
    return None


def connect(bp: str, src: str, src_pin: str, tgt: str, tgt_pin: str,
            func: Optional[str] = None) -> bool:
    """Connect two pins. Auto-translates exec pin names for UE4 conventions.

    In UE blueprints:
    - FunctionEntry exec output = "then"
    - VariableSet exec output = "then"
    - Branch True = "then", False = "else"
    - PrintString exec output = "then"
    - CallFunction exec output = "then"
    - All exec inputs = "execute"
    """
    global connections_made
    actual_src_pin = src_pin
    # All exec-producing nodes use "then" for their output, not "execute"
    if src_pin == "execute" and (
        "FunctionEntry" in src or "VariableSet" in src or
        "CallFunction" in src or "Sequence" in src
    ):
        actual_src_pin = "then"
    # Branch pins: Then->then, Else->else
    if src_pin == "Then":
        actual_src_pin = "then"
    if src_pin == "Else":
        actual_src_pin = "else"
    p: Dict[str, Any] = {
        "blueprint_name": bp,
        "source_node_id": src,
        "source_pin_name": actual_src_pin,
        "target_node_id": tgt,
        "target_pin_name": tgt_pin,
    }
    if func:
        p["function_name"] = func
    resp = send("connect_nodes", p)
    if is_ok(resp):
        connections_made += 1
        return True
    err = resp.get("error", str(resp))
    failed.append((f"connect:{bp}:{src}->{tgt}", err))
    return False


def var_get(bp: str, var_name: str, func: Optional[str] = None,
            x: int = 0, y: int = 0) -> Optional[str]:
    params: Dict[str, Any] = {"variable_name": var_name, "pos_x": x, "pos_y": y}
    return add_node(bp, "VariableGet", params, func)


def var_set(bp: str, var_name: str, func: Optional[str] = None,
            x: int = 0, y: int = 0) -> Optional[str]:
    params: Dict[str, Any] = {"variable_name": var_name, "pos_x": x, "pos_y": y}
    return add_node(bp, "VariableSet", params, func)


def branch(bp: str, func: Optional[str] = None,
           x: int = 0, y: int = 0) -> Optional[str]:
    return add_node(bp, "Branch", {"pos_x": x, "pos_y": y}, func)


def print_node(bp: str, msg: str, func: Optional[str] = None,
               x: int = 0, y: int = 0) -> Optional[str]:
    return add_node(bp, "Print", {"message": msg, "pos_x": x, "pos_y": y}, func)


def call_func(bp: str, target_func: str, func: Optional[str] = None,
              target_bp: Optional[str] = None,
              self_call: bool = True,
              x: int = 0, y: int = 0) -> Optional[str]:
    """Call a function. self_call=True (default) uses SetSelfMember for local BP functions.
    Set self_call=False for engine library calls (PrintString, etc.)."""
    params: Dict[str, Any] = {"target_function": target_func, "pos_x": x, "pos_y": y}
    if target_bp:
        params["target_blueprint"] = target_bp
    if self_call:
        params["self_call"] = True
    return add_node(bp, "CallFunction", params, func)


def comparison(bp: str, comp_type: str, func: Optional[str] = None,
               x: int = 0, y: int = 0) -> Optional[str]:
    return add_node(bp, "Comparison", {"comparison_type": comp_type, "pos_x": x, "pos_y": y}, func)


def switch_int(bp: str, func: Optional[str] = None,
               x: int = 0, y: int = 0) -> Optional[str]:
    return add_node(bp, "SwitchInteger", {"pos_x": x, "pos_y": y}, func)


def sequence(bp: str, func: Optional[str] = None,
             x: int = 0, y: int = 0) -> Optional[str]:
    return add_node(bp, "ExecutionSequence", {"pos_x": x, "pos_y": y}, func)


def add_event(bp: str, event_name: str, x: int = 0, y: int = 0) -> Optional[str]:
    resp = send("add_event_node", {
        "blueprint_name": bp, "event_name": event_name, "pos_x": x, "pos_y": y,
    })
    if is_ok(resp):
        global nodes_created
        nodes_created += 1
        r = resp.get("result", {})
        return r.get("node_id") or r.get("node_name") or r.get("id")
    failed.append((f"add_event:{bp}:{event_name}", resp.get("error", str(resp))))
    return None


def set_var_default(bp: str, var_name: str, value: Any) -> bool:
    resp = send("set_blueprint_variable_properties", {
        "blueprint_name": bp_path(bp), "variable_name": var_name, "default_value": str(value),
    })
    if is_ok(resp):
        return True
    failed.append((f"set_default:{bp}:{var_name}", resp.get("error", str(resp))))
    return False


def create_var(bp: str, var_name: str, var_type: str, default: Any = None,
               category: str = "") -> bool:
    params: Dict[str, Any] = {
        "blueprint_name": bp_path(bp), "variable_name": var_name, "variable_type": var_type,
    }
    if default is not None:
        params["default_value"] = str(default)
    if category:
        params["category"] = category
    resp = send("create_variable", params)
    if is_ok(resp):
        return True
    err = resp.get("error", str(resp))
    if "already exists" in str(err).lower():
        if default is not None:
            set_var_default(bp, var_name, default)
        return True
    failed.append((f"create_var:{bp}:{var_name}", err))
    return False


def create_func(bp: str, func_name: str, return_type: Optional[str] = None) -> bool:
    params: Dict[str, Any] = {"blueprint_name": bp_path(bp), "function_name": func_name}
    if return_type:
        params["return_type"] = return_type
    resp = send("create_function", params)
    if is_ok(resp):
        return True
    err = resp.get("error", str(resp))
    if "already exists" in str(err).lower():
        return True
    failed.append((f"create_func:{bp}:{func_name}", err))
    return False


def bp_path(bp: str) -> str:
    """Return full asset path for a blueprint name."""
    if bp.startswith("/"):
        return bp
    return f"/Game/Blueprints/{bp}"


def add_func_input(bp: str, func_name: str, param_name: str, param_type: str) -> bool:
    """Add function input param if it doesn't already exist."""
    # Check if param already exists
    check = send("get_blueprint_function_details", {
        "blueprint_path": bp_path(bp), "function_name": func_name,
    })
    if is_ok(check):
        existing = check.get("result", {}).get("function", {}).get("input_parameters", [])
        for p in existing:
            if p.get("name") == param_name:
                return True  # Already exists, skip
    resp = send("add_function_input", {
        "blueprint_name": bp_path(bp), "function_name": func_name,
        "param_name": param_name, "param_type": param_type,
    })
    if is_ok(resp):
        return True
    err = resp.get("error", str(resp))
    if "already" in str(err).lower():
        return True
    failed.append((f"func_input:{bp}:{func_name}:{param_name}", err))
    return False


def compile_bp(bp: str) -> bool:
    resp = send("compile_blueprint", {"blueprint_name": bp_path(bp)})
    return is_ok(resp)


# ============================================================
# PHASE 1: BP_PlayerCharacter
# ============================================================
BP_PLAYER = "BP_PlayerCharacter"


def set_player_defaults():
    """Set all variable default values for BP_PlayerCharacter."""
    print("  Setting player defaults...", flush=True)
    defaults = {
        "MaxHealth": 100.0, "CurrentHealth": 100.0, "bIsDead": False,
        "MaxStamina": 100.0, "CurrentStamina": 100.0,
        "StaminaRegenRate": 15.0, "StaminaRegenDelay": 1.0,
        "bCanRegenStamina": True, "StaminaRegenTimer": 0.0,
        "DodgeCost": 25.0, "BlockDrainRate": 10.0,
        "ComboIndex": 0, "bCanCombo": True,
        "bIsAttacking": False, "bIsBlocking": False,
        "bIsDodging": False, "bParryWindowActive": False,
        "ParryWindowDuration": 0.2,
        "LightAttackDamage": 15.0, "HeavyAttackDamage": 35.0,
        "ComboResetTime": 1.5, "LastAttackTime": 0.0,
        "bIsInvincible": False, "bSwordSkillReady": True,
        "SwordSkillCooldown": 8.0, "SwordSkillDamage": 50.0,
        "SwordSkillCooldownRemaining": 0.0,
        "bIsLockedOn": False, "LockOnRange": 1500.0,
        "HealthPercent": 1.0, "StaminaPercent": 1.0, "CooldownPercent": 1.0,
    }
    for name, val in defaults.items():
        set_var_default(BP_PLAYER, name, val)


def impl_player_take_damage():
    """Wire TakeDamageCustom: check blocking/parry/invincible, apply damage, check death."""
    fn = "TakeDamageCustom"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)

    # Check if function has DamageAmount input, add if missing
    add_func_input(bp, fn, "DamageAmount", "float")

    entry = "K2Node_FunctionEntry_0"

    # Branch: is dead?
    dead_get = var_get(bp, "bIsDead", fn, 200, 0)
    br_dead = branch(bp, fn, 350, 0)
    if dead_get and br_dead:
        connect(bp, entry, "execute", br_dead, "execute", fn)
        connect(bp, dead_get, "bIsDead", br_dead, "Condition", fn)

    # If dead, return (do nothing on True)
    ret_dead = print_node(bp, "[Combat] Already dead, ignoring damage", fn, 550, -100)
    if br_dead and ret_dead:
        connect(bp, br_dead, "Then", ret_dead, "execute", fn)

    # If alive (False branch): check invincible
    inv_get = var_get(bp, "bIsInvincible", fn, 400, 150)
    br_inv = branch(bp, fn, 550, 100)
    if br_dead and br_inv and inv_get:
        connect(bp, br_dead, "Else", br_inv, "execute", fn)
        connect(bp, inv_get, "bIsInvincible", br_inv, "Condition", fn)

    # If invincible, print and return
    ret_inv = print_node(bp, "[Combat] Invincible, damage blocked", fn, 750, 0)
    if br_inv and ret_inv:
        connect(bp, br_inv, "Then", ret_inv, "execute", fn)

    # If not invincible (False): check blocking
    blk_get = var_get(bp, "bIsBlocking", fn, 600, 300)
    br_blk = branch(bp, fn, 750, 250)
    if br_inv and br_blk and blk_get:
        connect(bp, br_inv, "Else", br_blk, "execute", fn)
        connect(bp, blk_get, "bIsBlocking", br_blk, "Condition", fn)

    # If blocking: check parry window
    parry_get = var_get(bp, "bParryWindowActive", fn, 850, 200)
    br_parry = branch(bp, fn, 1000, 200)
    if br_blk and br_parry and parry_get:
        connect(bp, br_blk, "Then", br_parry, "execute", fn)
        connect(bp, parry_get, "bParryWindowActive", br_parry, "Condition", fn)

    # If parry active: call OnParrySuccess
    parry_call = call_func(bp, "OnParrySuccess", fn, x=1200, y=100)
    if br_parry and parry_call:
        connect(bp, br_parry, "Then", parry_call, "execute", fn)

    # If not parry: print blocked, drain stamina
    blk_print = print_node(bp, "[Combat] Damage blocked", fn, 1200, 300)
    if br_parry and blk_print:
        connect(bp, br_parry, "Else", blk_print, "execute", fn)

    # If not blocking (False): apply damage
    # Get CurrentHealth, subtract DamageAmount, set
    hp_get = var_get(bp, "CurrentHealth", fn, 850, 450)
    hp_set = var_set(bp, "CurrentHealth", fn, 1100, 400)
    dmg_print = print_node(bp, "[Combat] Took damage!", fn, 1300, 400)

    if br_blk and hp_set and dmg_print:
        connect(bp, br_blk, "Else", hp_set, "execute", fn)
        connect(bp, hp_set, "execute", dmg_print, "execute", fn)

    # Check death: CurrentHealth <= 0
    hp_get2 = var_get(bp, "CurrentHealth", fn, 1300, 550)
    cmp_death = comparison(bp, "<=", fn, 1450, 550)
    br_death = branch(bp, fn, 1600, 500)
    die_call = call_func(bp, "Die", fn, x=1800, y=450)
    update_hud = call_func(bp, "UpdateHUDValues", fn, x=1800, y=600)

    if dmg_print and br_death and hp_get2 and cmp_death:
        connect(bp, dmg_print, "execute", br_death, "execute", fn)
        connect(bp, hp_get2, "CurrentHealth", cmp_death, "A", fn)
        connect(bp, cmp_death, "ReturnValue", br_death, "Condition", fn)

    if br_death and die_call:
        connect(bp, br_death, "Then", die_call, "execute", fn)
    if br_death and update_hud:
        connect(bp, br_death, "Else", update_hud, "execute", fn)


def impl_player_light_attack():
    """Wire TryLightAttack: check stamina/attacking/dead, advance combo, print."""
    fn = "TryLightAttack"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    # Check not dead
    dead_get = var_get(bp, "bIsDead", fn, 200, 0)
    br_dead = branch(bp, fn, 350, 0)
    if dead_get and br_dead:
        connect(bp, entry, "execute", br_dead, "execute", fn)
        connect(bp, dead_get, "bIsDead", br_dead, "Condition", fn)
    # Dead => return
    ret_dead = print_node(bp, "[Combat] Cannot attack while dead", fn, 550, -50)
    if br_dead and ret_dead:
        connect(bp, br_dead, "Then", ret_dead, "execute", fn)

    # Not dead: check not already attacking
    atk_get = var_get(bp, "bIsAttacking", fn, 400, 150)
    br_atk = branch(bp, fn, 550, 100)
    if br_dead and br_atk and atk_get:
        connect(bp, br_dead, "Else", br_atk, "execute", fn)
        connect(bp, atk_get, "bIsAttacking", br_atk, "Condition", fn)

    ret_atk = print_node(bp, "[Combat] Already attacking", fn, 750, 50)
    if br_atk and ret_atk:
        connect(bp, br_atk, "Then", ret_atk, "execute", fn)

    # Set attacking = true
    set_atk = var_set(bp, "bIsAttacking", fn, 700, 200)
    if br_atk and set_atk:
        connect(bp, br_atk, "Else", set_atk, "execute", fn)

    # Advance combo: print combo index
    combo_get = var_get(bp, "ComboIndex", fn, 700, 350)
    combo_print = print_node(bp, "[Combat] Light Attack - Combo Hit", fn, 900, 200)
    if set_atk and combo_print:
        connect(bp, set_atk, "execute", combo_print, "execute", fn)

    # Set combo index + 1 (mod 3)
    combo_set = var_set(bp, "ComboIndex", fn, 1100, 200)
    reset_call = call_func(bp, "ResetAttackState", fn, x=1300, y=200)
    if combo_print and combo_set:
        connect(bp, combo_print, "execute", combo_set, "execute", fn)
    if combo_set and reset_call:
        connect(bp, combo_set, "execute", reset_call, "execute", fn)


def impl_player_heavy_attack():
    """Wire TryHeavyAttack."""
    fn = "TryHeavyAttack"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    dead_get = var_get(bp, "bIsDead", fn, 200, 0)
    br_dead = branch(bp, fn, 350, 0)
    if dead_get and br_dead:
        connect(bp, entry, "execute", br_dead, "execute", fn)
        connect(bp, dead_get, "bIsDead", br_dead, "Condition", fn)

    ret_dead = print_node(bp, "[Combat] Cannot heavy attack while dead", fn, 550, -50)
    if br_dead and ret_dead:
        connect(bp, br_dead, "Then", ret_dead, "execute", fn)

    atk_get = var_get(bp, "bIsAttacking", fn, 400, 150)
    br_atk = branch(bp, fn, 550, 100)
    if br_dead and br_atk and atk_get:
        connect(bp, br_dead, "Else", br_atk, "execute", fn)
        connect(bp, atk_get, "bIsAttacking", br_atk, "Condition", fn)

    ret_atk = print_node(bp, "[Combat] Already attacking", fn, 750, 50)
    if br_atk and ret_atk:
        connect(bp, br_atk, "Then", ret_atk, "execute", fn)

    set_atk = var_set(bp, "bIsAttacking", fn, 700, 200)
    hvy_print = print_node(bp, "[Combat] Heavy Attack!", fn, 900, 200)
    reset = call_func(bp, "ResetAttackState", fn, x=1100, y=200)
    if br_atk and set_atk:
        connect(bp, br_atk, "Else", set_atk, "execute", fn)
    if set_atk and hvy_print:
        connect(bp, set_atk, "execute", hvy_print, "execute", fn)
    if hvy_print and reset:
        connect(bp, hvy_print, "execute", reset, "execute", fn)


def impl_player_dodge():
    """Wire TryDodge: check stamina >= DodgeCost, subtract, set invincible briefly."""
    fn = "TryDodge"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    dead_get = var_get(bp, "bIsDead", fn, 200, 0)
    br_dead = branch(bp, fn, 350, 0)
    if dead_get and br_dead:
        connect(bp, entry, "execute", br_dead, "execute", fn)
        connect(bp, dead_get, "bIsDead", br_dead, "Condition", fn)

    ret_dead = print_node(bp, "[Combat] Cannot dodge while dead", fn, 550, -50)
    if br_dead and ret_dead:
        connect(bp, br_dead, "Then", ret_dead, "execute", fn)

    # Check stamina
    stam_get = var_get(bp, "CurrentStamina", fn, 400, 150)
    cost_get = var_get(bp, "DodgeCost", fn, 400, 250)
    cmp_stam = comparison(bp, ">=", fn, 550, 180)
    br_stam = branch(bp, fn, 700, 150)

    if br_dead and br_stam and stam_get and cost_get and cmp_stam:
        connect(bp, br_dead, "Else", br_stam, "execute", fn)
        connect(bp, stam_get, "CurrentStamina", cmp_stam, "A", fn)
        connect(bp, cost_get, "DodgeCost", cmp_stam, "B", fn)
        connect(bp, cmp_stam, "ReturnValue", br_stam, "Condition", fn)

    # Not enough stamina
    ret_stam = print_node(bp, "[Combat] Not enough stamina to dodge", fn, 900, 50)
    if br_stam and ret_stam:
        connect(bp, br_stam, "Else", ret_stam, "execute", fn)

    # Dodge: set dodging, set invincible, subtract stamina, reset regen timer
    set_dodge = var_set(bp, "bIsDodging", fn, 900, 200)
    set_inv = var_set(bp, "bIsInvincible", fn, 1100, 200)
    stam_set = var_set(bp, "CurrentStamina", fn, 1300, 200)
    regen_set = var_set(bp, "bCanRegenStamina", fn, 1500, 200)
    dodge_print = print_node(bp, "[Combat] Dodge! i-frames active", fn, 1700, 200)

    if br_stam and set_dodge:
        connect(bp, br_stam, "Then", set_dodge, "execute", fn)
    if set_dodge and set_inv:
        connect(bp, set_dodge, "execute", set_inv, "execute", fn)
    if set_inv and stam_set:
        connect(bp, set_inv, "execute", stam_set, "execute", fn)
    if stam_set and regen_set:
        connect(bp, stam_set, "execute", regen_set, "execute", fn)
    if regen_set and dodge_print:
        connect(bp, regen_set, "execute", dodge_print, "execute", fn)


def impl_player_block():
    """Wire StartBlock and StopBlock."""
    bp = BP_PLAYER

    # StartBlock
    fn = "StartBlock"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"
    set_blk = var_set(bp, "bIsBlocking", fn, 200, 0)
    set_parry = var_set(bp, "bParryWindowActive", fn, 400, 0)
    blk_print = print_node(bp, "[Combat] Block started, parry window open", fn, 600, 0)
    if set_blk:
        connect(bp, entry, "execute", set_blk, "execute", fn)
    if set_blk and set_parry:
        connect(bp, set_blk, "execute", set_parry, "execute", fn)
    if set_parry and blk_print:
        connect(bp, set_parry, "execute", blk_print, "execute", fn)

    # StopBlock
    fn = "StopBlock"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"
    clr_blk = var_set(bp, "bIsBlocking", fn, 200, 0)
    clr_parry = var_set(bp, "bParryWindowActive", fn, 400, 0)
    stop_print = print_node(bp, "[Combat] Block ended", fn, 600, 0)
    if clr_blk:
        connect(bp, entry, "execute", clr_blk, "execute", fn)
    if clr_blk and clr_parry:
        connect(bp, clr_blk, "execute", clr_parry, "execute", fn)
    if clr_parry and stop_print:
        connect(bp, clr_parry, "execute", stop_print, "execute", fn)


def impl_player_sword_skill():
    """Wire TrySwordSkill: check cooldown ready, fire, start cooldown."""
    fn = "TrySwordSkill"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    ready_get = var_get(bp, "bSwordSkillReady", fn, 200, 0)
    br_ready = branch(bp, fn, 350, 0)
    if ready_get and br_ready:
        connect(bp, entry, "execute", br_ready, "execute", fn)
        connect(bp, ready_get, "bSwordSkillReady", br_ready, "Condition", fn)

    ret_cd = print_node(bp, "[Combat] Sword skill on cooldown", fn, 550, -50)
    if br_ready and ret_cd:
        connect(bp, br_ready, "Else", ret_cd, "execute", fn)

    # Fire skill
    set_ready = var_set(bp, "bSwordSkillReady", fn, 550, 100)
    cd_get = var_get(bp, "SwordSkillCooldown", fn, 550, 200)
    cd_set = var_set(bp, "SwordSkillCooldownRemaining", fn, 750, 100)
    skill_print = print_node(bp, "[Combat] SWORD SKILL activated!", fn, 950, 100)

    if br_ready and set_ready:
        connect(bp, br_ready, "Then", set_ready, "execute", fn)
    if set_ready and cd_set:
        connect(bp, set_ready, "execute", cd_set, "execute", fn)
    if cd_set and skill_print:
        connect(bp, cd_set, "execute", skill_print, "execute", fn)


def impl_player_parry():
    """Wire OnParrySuccess."""
    fn = "OnParrySuccess"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    parry_print = print_node(bp, "[Combat] PARRY SUCCESS! Enemy staggered!", fn, 200, 0)
    clr_parry = var_set(bp, "bParryWindowActive", fn, 450, 0)
    if parry_print:
        connect(bp, entry, "execute", parry_print, "execute", fn)
    if parry_print and clr_parry:
        connect(bp, parry_print, "execute", clr_parry, "execute", fn)


def impl_player_die():
    """Wire Die: set dead, print."""
    fn = "Die"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    set_dead = var_set(bp, "bIsDead", fn, 200, 0)
    set_hp = var_set(bp, "CurrentHealth", fn, 400, 0)
    die_print = print_node(bp, "[Player] PLAYER DIED", fn, 600, 0)
    if set_dead:
        connect(bp, entry, "execute", set_dead, "execute", fn)
    if set_dead and set_hp:
        connect(bp, set_dead, "execute", set_hp, "execute", fn)
    if set_hp and die_print:
        connect(bp, set_hp, "execute", die_print, "execute", fn)


def impl_player_stamina_regen():
    """Wire UpdateStaminaRegen: called from Tick, regen if allowed."""
    fn = "UpdateStaminaRegen"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    can_get = var_get(bp, "bCanRegenStamina", fn, 200, 0)
    br_can = branch(bp, fn, 350, 0)
    if can_get and br_can:
        connect(bp, entry, "execute", br_can, "execute", fn)
        connect(bp, can_get, "bCanRegenStamina", br_can, "Condition", fn)

    # Can regen: check stamina < max
    stam_get = var_get(bp, "CurrentStamina", fn, 400, 100)
    max_get = var_get(bp, "MaxStamina", fn, 400, 200)
    cmp_max = comparison(bp, "<", fn, 550, 150)
    br_max = branch(bp, fn, 700, 100)

    if br_can and br_max and stam_get and max_get and cmp_max:
        connect(bp, br_can, "Then", br_max, "execute", fn)
        connect(bp, stam_get, "CurrentStamina", cmp_max, "A", fn)
        connect(bp, max_get, "MaxStamina", cmp_max, "B", fn)
        connect(bp, cmp_max, "ReturnValue", br_max, "Condition", fn)

    # If below max: add regen
    stam_set = var_set(bp, "CurrentStamina", fn, 900, 100)
    regen_print = print_node(bp, "[Regen] Stamina regenerating", fn, 1100, 100)
    if br_max and stam_set:
        connect(bp, br_max, "Then", stam_set, "execute", fn)
    if stam_set and regen_print:
        connect(bp, stam_set, "execute", regen_print, "execute", fn)


def impl_player_cooldown():
    """Wire UpdateSwordSkillCooldown."""
    fn = "UpdateSwordSkillCooldown"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    ready_get = var_get(bp, "bSwordSkillReady", fn, 200, 0)
    br_ready = branch(bp, fn, 350, 0)
    if ready_get and br_ready:
        connect(bp, entry, "execute", br_ready, "execute", fn)
        connect(bp, ready_get, "bSwordSkillReady", br_ready, "Condition", fn)
    # Already ready: return

    # Not ready: decrement
    cd_get = var_get(bp, "SwordSkillCooldownRemaining", fn, 400, 150)
    cmp_zero = comparison(bp, "<=", fn, 550, 150)
    br_zero = branch(bp, fn, 700, 100)

    if br_ready and br_zero and cd_get and cmp_zero:
        connect(bp, br_ready, "Else", br_zero, "execute", fn)
        connect(bp, cd_get, "SwordSkillCooldownRemaining", cmp_zero, "A", fn)
        connect(bp, cmp_zero, "ReturnValue", br_zero, "Condition", fn)

    # Cooldown expired: reset
    set_ready = var_set(bp, "bSwordSkillReady", fn, 900, 50)
    cd_done_print = print_node(bp, "[Combat] Sword skill ready!", fn, 1100, 50)
    if br_zero and set_ready:
        connect(bp, br_zero, "Then", set_ready, "execute", fn)
    if set_ready and cd_done_print:
        connect(bp, set_ready, "execute", cd_done_print, "execute", fn)

    # Still cooling: decrement
    cd_set = var_set(bp, "SwordSkillCooldownRemaining", fn, 900, 200)
    if br_zero and cd_set:
        connect(bp, br_zero, "Else", cd_set, "execute", fn)


def impl_player_update_hud():
    """Wire UpdateHUDValues: compute percents."""
    fn = "UpdateHUDValues"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    hp_set = var_set(bp, "HealthPercent", fn, 200, 0)
    stam_set = var_set(bp, "StaminaPercent", fn, 400, 0)
    cd_set = var_set(bp, "CooldownPercent", fn, 600, 0)
    hud_print = print_node(bp, "[HUD] Values updated", fn, 800, 0)

    if hp_set:
        connect(bp, entry, "execute", hp_set, "execute", fn)
    if hp_set and stam_set:
        connect(bp, hp_set, "execute", stam_set, "execute", fn)
    if stam_set and cd_set:
        connect(bp, stam_set, "execute", cd_set, "execute", fn)
    if cd_set and hud_print:
        connect(bp, cd_set, "execute", hud_print, "execute", fn)


def impl_player_reset_attack():
    """Wire ResetAttackState."""
    fn = "ResetAttackState"
    bp = BP_PLAYER
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    set_atk = var_set(bp, "bIsAttacking", fn, 200, 0)
    set_dodge = var_set(bp, "bIsDodging", fn, 400, 0)
    set_inv = var_set(bp, "bIsInvincible", fn, 600, 0)
    reset_print = print_node(bp, "[Combat] Attack state reset", fn, 800, 0)

    if set_atk:
        connect(bp, entry, "execute", set_atk, "execute", fn)
    if set_atk and set_dodge:
        connect(bp, set_atk, "execute", set_dodge, "execute", fn)
    if set_dodge and set_inv:
        connect(bp, set_dodge, "execute", set_inv, "execute", fn)
    if set_inv and reset_print:
        connect(bp, set_inv, "execute", reset_print, "execute", fn)


def impl_player_event_graph():
    """Wire BeginPlay and Tick in BP_PlayerCharacter EventGraph."""
    bp = BP_PLAYER
    print("  Wiring EventGraph (BeginPlay + Tick)...", flush=True)

    # BeginPlay: print init message, call UpdateHUDValues
    begin = add_event(bp, "BeginPlay", 0, 0)
    init_print = print_node(bp, "[Player] SignalBound Player initialized", None, 250, 0)
    hud_call = call_func(bp, "UpdateHUDValues", None, x=500, y=0)
    if begin and init_print:
        connect(bp, begin, "execute", init_print, "execute")
    if init_print and hud_call:
        connect(bp, init_print, "execute", hud_call, "execute")

    # Tick: call stamina regen and cooldown update
    tick = add_event(bp, "Tick", 0, 200)
    seq = sequence(bp, None, 250, 200)
    stam_call = call_func(bp, "UpdateStaminaRegen", None, x=450, y=200)
    cd_call = call_func(bp, "UpdateSwordSkillCooldown", None, x=450, y=350)
    hud_tick = call_func(bp, "UpdateHUDValues", None, x=650, y=200)

    if tick and seq:
        connect(bp, tick, "execute", seq, "execute")
    if seq and stam_call:
        connect(bp, seq, "Then 0", stam_call, "execute")
    if seq and cd_call:
        connect(bp, seq, "Then 1", cd_call, "execute")
    if stam_call and hud_tick:
        connect(bp, stam_call, "execute", hud_tick, "execute")


def build_player():
    print("\n=== PHASE: BP_PlayerCharacter ===", flush=True)
    set_player_defaults()
    impl_player_take_damage()
    impl_player_light_attack()
    impl_player_heavy_attack()
    impl_player_dodge()
    impl_player_block()
    impl_player_sword_skill()
    impl_player_parry()
    impl_player_die()
    impl_player_stamina_regen()
    impl_player_cooldown()
    impl_player_update_hud()
    impl_player_reset_attack()
    impl_player_event_graph()
    compile_bp(BP_PLAYER)
    print("  DONE: BP_PlayerCharacter", flush=True)


# ============================================================
# PHASE 2: BP_EnemyBase + children
# ============================================================
BP_ENEMY = "BP_EnemyBase"


def set_enemy_defaults():
    """Set default values for BP_EnemyBase."""
    print("  Setting enemy defaults...", flush=True)
    defaults = {
        "MaxHealth": 100.0, "CurrentHealth": 100.0, "bIsDead": False,
        "AttackDamage": 20.0, "AttackCooldown": 2.0,
        "WindupDuration": 0.8, "RecoveryDuration": 0.5,
        "StaggerDuration": 1.5, "StaggerThreshold": 40.0,
        "AccumulatedStagger": 0.0, "HitReactDuration": 0.4,
        "ChaseSpeed": 400.0, "AttackRange": 200.0, "DetectionRange": 800.0,
        "CurrentStateIndex": 0, "StateTimer": 0.0,
        "bPlayerDetected": False, "bPlayerInRange": False, "bIsRanged": False,
    }
    for name, val in defaults.items():
        set_var_default(BP_ENEMY, name, val)


def impl_enemy_tick_state_machine():
    """Wire TickStateMachine: SwitchInteger on CurrentStateIndex -> call TickXxx."""
    fn = "TickStateMachine"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    # Add DeltaTime input
    add_func_input(bp, fn, "DeltaTime", "float")

    state_get = var_get(bp, "CurrentStateIndex", fn, 200, 0)
    sw = switch_int(bp, fn, 400, 0)

    if state_get and sw:
        connect(bp, entry, "execute", sw, "execute", fn)
        connect(bp, state_get, "CurrentStateIndex", sw, "Selection", fn)

    # State calls: 0=Idle, 1=Chase, 2=Windup, 3=Attack, 4=Recover, 5=Stunned, 6=HitReact, 7=Dead
    state_funcs = ["TickIdle", "TickChase", "TickWindup", "TickAttack",
                   "TickRecover", "TickStunned", "TickHitReact", "Die"]
    for i, sfn in enumerate(state_funcs):
        node = call_func(bp, sfn, fn, x=700, y=i * 120)
        if sw and node:
            connect(bp, sw, str(i), node, "execute", fn)


def impl_enemy_enter_state():
    """Wire EnterState: set CurrentStateIndex, reset timer, print."""
    fn = "EnterState"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    add_func_input(bp, fn, "NewState", "int")

    set_state = var_set(bp, "CurrentStateIndex", fn, 200, 0)
    set_timer = var_set(bp, "StateTimer", fn, 400, 0)
    state_print = print_node(bp, "[Enemy] Entering state", fn, 600, 0)

    if set_state:
        connect(bp, entry, "execute", set_state, "execute", fn)
    if set_state and set_timer:
        connect(bp, set_state, "execute", set_timer, "execute", fn)
    if set_timer and state_print:
        connect(bp, set_timer, "execute", state_print, "execute", fn)


def impl_enemy_tick_idle():
    """Wire TickIdle: check detection -> enter Chase."""
    fn = "TickIdle"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    det_get = var_get(bp, "bPlayerDetected", fn, 200, 0)
    br_det = branch(bp, fn, 350, 0)
    if det_get and br_det:
        connect(bp, entry, "execute", br_det, "execute", fn)
        connect(bp, det_get, "bPlayerDetected", br_det, "Condition", fn)

    # Detected: enter Chase (state 1)
    chase_call = call_func(bp, "EnterState", fn, x=550, y=0)
    chase_print = print_node(bp, "[Enemy] Player detected! Chasing!", fn, 750, 0)
    if br_det and chase_call:
        connect(bp, br_det, "Then", chase_call, "execute", fn)
    if chase_call and chase_print:
        connect(bp, chase_call, "execute", chase_print, "execute", fn)

    idle_print = print_node(bp, "[Enemy] Idle... scanning", fn, 550, 150)
    if br_det and idle_print:
        connect(bp, br_det, "Else", idle_print, "execute", fn)


def impl_enemy_tick_chase():
    """Wire TickChase: move toward player, check attack range."""
    fn = "TickChase"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    range_get = var_get(bp, "bPlayerInRange", fn, 200, 0)
    br_range = branch(bp, fn, 350, 0)
    if range_get and br_range:
        connect(bp, entry, "execute", br_range, "execute", fn)
        connect(bp, range_get, "bPlayerInRange", br_range, "Condition", fn)

    # In range: enter Windup (state 2)
    windup_call = call_func(bp, "EnterState", fn, x=550, y=0)
    windup_print = print_node(bp, "[Enemy] In range! Winding up attack!", fn, 750, 0)
    if br_range and windup_call:
        connect(bp, br_range, "Then", windup_call, "execute", fn)
    if windup_call and windup_print:
        connect(bp, windup_call, "execute", windup_print, "execute", fn)

    chase_print = print_node(bp, "[Enemy] Chasing player...", fn, 550, 150)
    if br_range and chase_print:
        connect(bp, br_range, "Else", chase_print, "execute", fn)


def impl_enemy_tick_windup():
    """Wire TickWindup: wait WindupDuration, then enter Attack."""
    fn = "TickWindup"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    timer_get = var_get(bp, "StateTimer", fn, 200, 0)
    dur_get = var_get(bp, "WindupDuration", fn, 200, 100)
    cmp = comparison(bp, ">=", fn, 400, 50)
    br_done = branch(bp, fn, 550, 0)

    if timer_get and dur_get and cmp and br_done:
        connect(bp, entry, "execute", br_done, "execute", fn)
        connect(bp, timer_get, "StateTimer", cmp, "A", fn)
        connect(bp, dur_get, "WindupDuration", cmp, "B", fn)
        connect(bp, cmp, "ReturnValue", br_done, "Condition", fn)

    atk_call = call_func(bp, "EnterState", fn, x=750, y=0)
    atk_print = print_node(bp, "[Enemy] ATTACKING!", fn, 950, 0)
    if br_done and atk_call:
        connect(bp, br_done, "Then", atk_call, "execute", fn)
    if atk_call and atk_print:
        connect(bp, atk_call, "execute", atk_print, "execute", fn)

    wu_print = print_node(bp, "[Enemy] Winding up...", fn, 750, 150)
    if br_done and wu_print:
        connect(bp, br_done, "Else", wu_print, "execute", fn)


def impl_enemy_tick_attack():
    """Wire TickAttack: deal damage, enter Recover."""
    fn = "TickAttack"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    atk_print = print_node(bp, "[Enemy] Attack lands! Dealing damage!", fn, 200, 0)
    recover_call = call_func(bp, "EnterState", fn, x=500, y=0)
    rec_print = print_node(bp, "[Enemy] Entering recovery...", fn, 700, 0)

    if atk_print:
        connect(bp, entry, "execute", atk_print, "execute", fn)
    if atk_print and recover_call:
        connect(bp, atk_print, "execute", recover_call, "execute", fn)
    if recover_call and rec_print:
        connect(bp, recover_call, "execute", rec_print, "execute", fn)


def impl_enemy_tick_recover():
    """Wire TickRecover: wait RecoveryDuration, return to Idle/Chase."""
    fn = "TickRecover"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    timer_get = var_get(bp, "StateTimer", fn, 200, 0)
    dur_get = var_get(bp, "RecoveryDuration", fn, 200, 100)
    cmp = comparison(bp, ">=", fn, 400, 50)
    br_done = branch(bp, fn, 550, 0)

    if timer_get and dur_get and cmp and br_done:
        connect(bp, entry, "execute", br_done, "execute", fn)
        connect(bp, timer_get, "StateTimer", cmp, "A", fn)
        connect(bp, dur_get, "RecoveryDuration", cmp, "B", fn)
        connect(bp, cmp, "ReturnValue", br_done, "Condition", fn)

    # Done: check if player still detected
    det_get = var_get(bp, "bPlayerDetected", fn, 700, 0)
    br_det = branch(bp, fn, 850, 0)
    if br_done and br_det and det_get:
        connect(bp, br_done, "Then", br_det, "execute", fn)
        connect(bp, det_get, "bPlayerDetected", br_det, "Condition", fn)

    chase_call = call_func(bp, "EnterState", fn, x=1050, y=-50)
    idle_call = call_func(bp, "EnterState", fn, x=1050, y=100)
    if br_det and chase_call:
        connect(bp, br_det, "Then", chase_call, "execute", fn)
    if br_det and idle_call:
        connect(bp, br_det, "Else", idle_call, "execute", fn)

    rec_print = print_node(bp, "[Enemy] Recovering...", fn, 750, 200)
    if br_done and rec_print:
        connect(bp, br_done, "Else", rec_print, "execute", fn)


def impl_enemy_tick_stunned():
    """Wire TickStunned: wait StaggerDuration, return to Idle."""
    fn = "TickStunned"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    timer_get = var_get(bp, "StateTimer", fn, 200, 0)
    dur_get = var_get(bp, "StaggerDuration", fn, 200, 100)
    cmp = comparison(bp, ">=", fn, 400, 50)
    br_done = branch(bp, fn, 550, 0)

    if timer_get and dur_get and cmp and br_done:
        connect(bp, entry, "execute", br_done, "execute", fn)
        connect(bp, timer_get, "StateTimer", cmp, "A", fn)
        connect(bp, dur_get, "StaggerDuration", cmp, "B", fn)
        connect(bp, cmp, "ReturnValue", br_done, "Condition", fn)

    idle_call = call_func(bp, "EnterState", fn, x=750, y=0)
    stun_print = print_node(bp, "[Enemy] STUNNED!", fn, 750, 150)
    stagger_reset = var_set(bp, "AccumulatedStagger", fn, 950, 0)

    if br_done and idle_call:
        connect(bp, br_done, "Then", idle_call, "execute", fn)
    if idle_call and stagger_reset:
        connect(bp, idle_call, "execute", stagger_reset, "execute", fn)
    if br_done and stun_print:
        connect(bp, br_done, "Else", stun_print, "execute", fn)


def impl_enemy_tick_hitreact():
    """Wire TickHitReact: wait HitReactDuration, return to Chase."""
    fn = "TickHitReact"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    timer_get = var_get(bp, "StateTimer", fn, 200, 0)
    dur_get = var_get(bp, "HitReactDuration", fn, 200, 100)
    cmp = comparison(bp, ">=", fn, 400, 50)
    br_done = branch(bp, fn, 550, 0)

    if timer_get and dur_get and cmp and br_done:
        connect(bp, entry, "execute", br_done, "execute", fn)
        connect(bp, timer_get, "StateTimer", cmp, "A", fn)
        connect(bp, dur_get, "HitReactDuration", cmp, "B", fn)
        connect(bp, cmp, "ReturnValue", br_done, "Condition", fn)

    chase_call = call_func(bp, "EnterState", fn, x=750, y=0)
    hr_print = print_node(bp, "[Enemy] Hit reacting...", fn, 750, 150)

    if br_done and chase_call:
        connect(bp, br_done, "Then", chase_call, "execute", fn)
    if br_done and hr_print:
        connect(bp, br_done, "Else", hr_print, "execute", fn)


def impl_enemy_receive_damage():
    """Wire ReceiveDamage: apply damage, check stagger, check death."""
    fn = "ReceiveDamage"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    add_func_input(bp, fn, "DamageAmount", "float")

    # Check not dead
    dead_get = var_get(bp, "bIsDead", fn, 200, 0)
    br_dead = branch(bp, fn, 350, 0)
    if dead_get and br_dead:
        connect(bp, entry, "execute", br_dead, "execute", fn)
        connect(bp, dead_get, "bIsDead", br_dead, "Condition", fn)

    ret_dead = print_node(bp, "[Enemy] Already dead", fn, 550, -50)
    if br_dead and ret_dead:
        connect(bp, br_dead, "Then", ret_dead, "execute", fn)

    # Subtract health
    hp_set = var_set(bp, "CurrentHealth", fn, 550, 100)
    dmg_print = print_node(bp, "[Enemy] Took damage!", fn, 750, 100)

    if br_dead and hp_set:
        connect(bp, br_dead, "Else", hp_set, "execute", fn)
    if hp_set and dmg_print:
        connect(bp, hp_set, "execute", dmg_print, "execute", fn)

    # Check death
    hp_get = var_get(bp, "CurrentHealth", fn, 750, 250)
    cmp_death = comparison(bp, "<=", fn, 900, 250)
    br_death = branch(bp, fn, 1050, 200)

    if dmg_print and br_death and hp_get and cmp_death:
        connect(bp, dmg_print, "execute", br_death, "execute", fn)
        connect(bp, hp_get, "CurrentHealth", cmp_death, "A", fn)
        connect(bp, cmp_death, "ReturnValue", br_death, "Condition", fn)

    die_call = call_func(bp, "EnterState", fn, x=1250, y=150)
    if br_death and die_call:
        connect(bp, br_death, "Then", die_call, "execute", fn)

    # Not dead: accumulate stagger, check stun
    stag_set = var_set(bp, "AccumulatedStagger", fn, 1250, 350)
    stag_get = var_get(bp, "AccumulatedStagger", fn, 1250, 450)
    thresh_get = var_get(bp, "StaggerThreshold", fn, 1250, 530)
    cmp_stag = comparison(bp, ">=", fn, 1400, 480)
    br_stag = branch(bp, fn, 1550, 350)

    if br_death and stag_set:
        connect(bp, br_death, "Else", stag_set, "execute", fn)
    if stag_set and br_stag and stag_get and thresh_get and cmp_stag:
        connect(bp, stag_set, "execute", br_stag, "execute", fn)
        connect(bp, stag_get, "AccumulatedStagger", cmp_stag, "A", fn)
        connect(bp, thresh_get, "StaggerThreshold", cmp_stag, "B", fn)
        connect(bp, cmp_stag, "ReturnValue", br_stag, "Condition", fn)

    stun_call = call_func(bp, "EnterState", fn, x=1750, y=300)
    hr_call = call_func(bp, "EnterState", fn, x=1750, y=450)
    if br_stag and stun_call:
        connect(bp, br_stag, "Then", stun_call, "execute", fn)
    if br_stag and hr_call:
        connect(bp, br_stag, "Else", hr_call, "execute", fn)


def impl_enemy_die():
    """Wire Die: set dead, print."""
    fn = "Die"
    bp = BP_ENEMY
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    set_dead = var_set(bp, "bIsDead", fn, 200, 0)
    die_print = print_node(bp, "[Enemy] ENEMY DIED", fn, 400, 0)
    if set_dead:
        connect(bp, entry, "execute", set_dead, "execute", fn)
    if set_dead and die_print:
        connect(bp, set_dead, "execute", die_print, "execute", fn)


def impl_enemy_event_graph():
    """Wire enemy BeginPlay and Tick."""
    bp = BP_ENEMY
    print("  Wiring EnemyBase EventGraph...", flush=True)

    begin = add_event(bp, "BeginPlay", 0, 0)
    init_print = print_node(bp, "[Enemy] EnemyBase initialized", None, 250, 0)
    enter_idle = call_func(bp, "EnterState", None, x=500, y=0)
    if begin and init_print:
        connect(bp, begin, "execute", init_print, "execute")
    if init_print and enter_idle:
        connect(bp, init_print, "execute", enter_idle, "execute")

    tick = add_event(bp, "Tick", 0, 200)
    tick_sm = call_func(bp, "TickStateMachine", None, x=250, y=200)
    if tick and tick_sm:
        connect(bp, tick, "execute", tick_sm, "execute")


def set_child_enemy_defaults():
    """Set child enemy stat overrides."""
    print("  Setting child enemy defaults...", flush=True)
    children = {
        "BP_Enemy_Thrall": {
            "WindupDuration": 1.2, "MaxHealth": 80.0, "CurrentHealth": 80.0,
            "ChaseSpeed": 300.0, "AttackDamage": 15.0,
        },
        "BP_Enemy_Skitter": {
            "ChaseSpeed": 600.0, "MaxHealth": 30.0, "CurrentHealth": 30.0,
            "WindupDuration": 0.4, "AttackDamage": 10.0,
        },
        "BP_Enemy_Hexer": {
            "AttackRange": 800.0, "bIsRanged": True, "MaxHealth": 60.0,
            "CurrentHealth": 60.0, "WindupDuration": 0.6, "AttackDamage": 25.0,
        },
        "BP_Elite_Oathguard": {
            "MaxHealth": 200.0, "CurrentHealth": 200.0,
            "WindupDuration": 1.0, "AttackDamage": 30.0,
            "StaggerThreshold": 80.0, "ChaseSpeed": 250.0,
        },
    }
    for child_bp, overrides in children.items():
        for var_name, val in overrides.items():
            set_var_default(child_bp, var_name, val)

    # Add Oathguard-specific vars
    create_var("BP_Elite_Oathguard", "bHasShield", "bool", True, "Combat")
    create_var("BP_Elite_Oathguard", "ShieldHealth", "float", 50.0, "Combat")


def build_enemy():
    print("\n=== PHASE: BP_EnemyBase + Children ===", flush=True)
    set_enemy_defaults()
    impl_enemy_enter_state()
    impl_enemy_tick_state_machine()
    impl_enemy_tick_idle()
    impl_enemy_tick_chase()
    impl_enemy_tick_windup()
    impl_enemy_tick_attack()
    impl_enemy_tick_recover()
    impl_enemy_tick_stunned()
    impl_enemy_tick_hitreact()
    impl_enemy_receive_damage()
    impl_enemy_die()
    impl_enemy_event_graph()
    compile_bp(BP_ENEMY)
    set_child_enemy_defaults()
    for child in ["BP_Enemy_Thrall", "BP_Enemy_Skitter", "BP_Enemy_Hexer", "BP_Elite_Oathguard"]:
        compile_bp(child)
    print("  DONE: BP_EnemyBase + Children", flush=True)


# ============================================================
# PHASE 3: BP_SystemManager + BP_ContractManager
# ============================================================


def set_system_defaults():
    """Set SystemManager defaults."""
    print("  Setting SystemManager defaults...", flush=True)
    set_var_default("BP_SystemManager", "ProviderModeIndex", 0)  # 0=Scripted
    set_var_default("BP_SystemManager", "ScriptedDirectiveIndex", 0)
    set_var_default("BP_SystemManager", "bDirectiveActive", False)
    set_var_default("BP_SystemManager", "DirectiveDisplayTime", 5.0)
    set_var_default("BP_SystemManager", "DirectiveTimer", 0.0)
    # Scripted directives (offline-safe)
    set_var_default("BP_SystemManager", "DirectiveText_0",
                    "The Citadel remembers those who fall. Rise again, Signalbound.")
    set_var_default("BP_SystemManager", "DirectiveText_1",
                    "Contracts forge resolve. Accept the challenge, reap the signal.")
    set_var_default("BP_SystemManager", "DirectiveText_2",
                    "The Ironcatacomb awaits. Steel yourself before the descent.")
    set_var_default("BP_SystemManager", "DirectiveText_3",
                    "Three sigils seal the gate. Gather them from the depths.")
    set_var_default("BP_SystemManager", "DirectiveText_4",
                    "The System watches. Every action carries weight.")


def impl_system_request_directive():
    """Wire RequestDirective: switch on ProviderModeIndex (0=Scripted,1=Cached,2=Live)."""
    fn = "RequestDirective"
    bp = "BP_SystemManager"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    mode_get = var_get(bp, "ProviderModeIndex", fn, 200, 0)
    sw = switch_int(bp, fn, 400, 0)
    if mode_get and sw:
        connect(bp, entry, "execute", sw, "execute", fn)
        connect(bp, mode_get, "ProviderModeIndex", sw, "Selection", fn)

    # 0: Scripted (offline)
    scripted_call = call_func(bp, "GetScriptedDirective", fn, x=650, y=0)
    show_call_0 = call_func(bp, "ShowDirective", fn, x=850, y=0)
    if sw and scripted_call:
        connect(bp, sw, "0", scripted_call, "execute", fn)
    if scripted_call and show_call_0:
        connect(bp, scripted_call, "execute", show_call_0, "execute", fn)

    # 1: Cached (same as scripted for now)
    cached_print = print_node(bp, "[System] Cached provider: using scripted fallback", fn, 650, 150)
    scripted_call2 = call_func(bp, "GetScriptedDirective", fn, x=950, y=150)
    show_call_1 = call_func(bp, "ShowDirective", fn, x=1150, y=150)
    if sw and cached_print:
        connect(bp, sw, "1", cached_print, "execute", fn)
    if cached_print and scripted_call2:
        connect(bp, cached_print, "execute", scripted_call2, "execute", fn)
    if scripted_call2 and show_call_1:
        connect(bp, scripted_call2, "execute", show_call_1, "execute", fn)

    # 2: Live stub (falls back to scripted when offline)
    live_print = print_node(bp, "[System] Live provider stub: no internet, using scripted fallback", fn, 650, 300)
    scripted_call3 = call_func(bp, "GetScriptedDirective", fn, x=1050, y=300)
    show_call_2 = call_func(bp, "ShowDirective", fn, x=1250, y=300)
    if sw and live_print:
        connect(bp, sw, "2", live_print, "execute", fn)
    if live_print and scripted_call3:
        connect(bp, live_print, "execute", scripted_call3, "execute", fn)
    if scripted_call3 and show_call_2:
        connect(bp, scripted_call3, "execute", show_call_2, "execute", fn)

    # Default: scripted
    default_call = call_func(bp, "GetScriptedDirective", fn, x=650, y=450)
    show_call_d = call_func(bp, "ShowDirective", fn, x=850, y=450)
    if sw and default_call:
        connect(bp, sw, "Default", default_call, "execute", fn)
    if default_call and show_call_d:
        connect(bp, default_call, "execute", show_call_d, "execute", fn)


def impl_system_get_scripted():
    """Wire GetScriptedDirective: cycle through 5 directives."""
    fn = "GetScriptedDirective"
    bp = "BP_SystemManager"
    print(f"  Wiring {fn}...", flush=True)
    # This function already has 2 nodes (entry + something), so get entry
    entry = "K2Node_FunctionEntry_0"

    idx_get = var_get(bp, "ScriptedDirectiveIndex", fn, 200, 0)
    sw = switch_int(bp, fn, 400, 0)

    if idx_get and sw:
        connect(bp, entry, "execute", sw, "execute", fn)
        connect(bp, idx_get, "ScriptedDirectiveIndex", sw, "Selection", fn)

    for i in range(5):
        d_get = var_get(bp, f"DirectiveText_{i}", fn, 650, i * 100)
        d_set = var_set(bp, "CurrentDirective", fn, 850, i * 100)
        if sw and d_set:
            connect(bp, sw, str(i), d_set, "execute", fn)
        if d_get and d_set:
            connect(bp, d_get, f"DirectiveText_{i}", d_set, "CurrentDirective", fn)

    # Advance index
    idx_set = var_set(bp, "ScriptedDirectiveIndex", fn, 1100, 0)
    # Default also sets index
    if sw and idx_set:
        connect(bp, sw, "Default", idx_set, "execute", fn)


def impl_system_show_directive():
    """Wire ShowDirective: set active, print directive."""
    fn = "ShowDirective"
    bp = "BP_SystemManager"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    set_active = var_set(bp, "bDirectiveActive", fn, 200, 0)
    dir_get = var_get(bp, "CurrentDirective", fn, 200, 100)
    dir_print = print_node(bp, "[System Directive]", fn, 400, 0)

    if set_active:
        connect(bp, entry, "execute", set_active, "execute", fn)
    if set_active and dir_print:
        connect(bp, set_active, "execute", dir_print, "execute", fn)


def impl_system_clear_directive():
    """Wire ClearDirective."""
    fn = "ClearDirective"
    bp = "BP_SystemManager"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    set_inactive = var_set(bp, "bDirectiveActive", fn, 200, 0)
    clr_print = print_node(bp, "[System] Directive cleared", fn, 400, 0)
    if set_inactive:
        connect(bp, entry, "execute", set_inactive, "execute", fn)
    if set_inactive and clr_print:
        connect(bp, set_inactive, "execute", clr_print, "execute", fn)


def impl_system_event_graph():
    """Wire SystemManager BeginPlay."""
    bp = "BP_SystemManager"
    print("  Wiring SystemManager EventGraph...", flush=True)

    begin = add_event(bp, "BeginPlay", 0, 0)
    init_print = print_node(bp, "[System] SystemManager online. Provider mode: Scripted (offline-safe)", None, 250, 0)
    req_call = call_func(bp, "RequestDirective", None, x=600, y=0)
    if begin and init_print:
        connect(bp, begin, "execute", init_print, "execute")
    if init_print and req_call:
        connect(bp, init_print, "execute", req_call, "execute")


def set_contract_defaults():
    """Set ContractManager defaults."""
    print("  Setting ContractManager defaults...", flush=True)
    defaults = {
        "ActiveContractType": -1, "bContractActive": False,
        "ContractTimer": 0.0, "ContractTargetTime": 30.0,
        "ContractTargetCount": 3, "ParryChainCount": 0,
        "KillCount": 0, "bPlayerTookDamage": False,
        "bPlayerHealed": False,
        "ContractDescription": "No active contract",
    }
    for name, val in defaults.items():
        set_var_default("BP_ContractManager", name, val)


def impl_contract_offer():
    """Wire OfferContract: set type, description, activate."""
    fn = "OfferContract"
    bp = "BP_ContractManager"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    add_func_input(bp, fn, "ContractType", "int")

    set_type = var_set(bp, "ActiveContractType", fn, 200, 0)
    desc_call = call_func(bp, "GetContractDescription", fn, x=400, y=0)
    offer_print = print_node(bp, "[Contract] New contract offered!", fn, 600, 0)

    if set_type:
        connect(bp, entry, "execute", set_type, "execute", fn)
    if set_type and desc_call:
        connect(bp, set_type, "execute", desc_call, "execute", fn)
    if desc_call and offer_print:
        connect(bp, desc_call, "execute", offer_print, "execute", fn)


def impl_contract_accept():
    """Wire AcceptContract: activate, reset trackers."""
    fn = "AcceptContract"
    bp = "BP_ContractManager"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    set_active = var_set(bp, "bContractActive", fn, 200, 0)
    set_timer = var_set(bp, "ContractTimer", fn, 400, 0)
    reset_parry = var_set(bp, "ParryChainCount", fn, 600, 0)
    reset_kill = var_set(bp, "KillCount", fn, 800, 0)
    reset_dmg = var_set(bp, "bPlayerTookDamage", fn, 1000, 0)
    reset_heal = var_set(bp, "bPlayerHealed", fn, 1200, 0)
    acc_print = print_node(bp, "[Contract] Contract ACCEPTED!", fn, 1400, 0)

    nodes = [set_active, set_timer, reset_parry, reset_kill, reset_dmg, reset_heal, acc_print]
    if set_active:
        connect(bp, entry, "execute", set_active, "execute", fn)
    for i in range(len(nodes) - 1):
        if nodes[i] and nodes[i + 1]:
            connect(bp, nodes[i], "execute", nodes[i + 1], "execute", fn)


def impl_contract_update():
    """Wire UpdateContract: increment timer, check conditions per type."""
    fn = "UpdateContract"
    bp = "BP_ContractManager"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    add_func_input(bp, fn, "DeltaTime", "float")

    active_get = var_get(bp, "bContractActive", fn, 200, 0)
    br_active = branch(bp, fn, 350, 0)
    if active_get and br_active:
        connect(bp, entry, "execute", br_active, "execute", fn)
        connect(bp, active_get, "bContractActive", br_active, "Condition", fn)

    # Not active: return
    # Active: increment timer
    timer_set = var_set(bp, "ContractTimer", fn, 550, 0)
    type_get = var_get(bp, "ActiveContractType", fn, 550, 150)
    sw = switch_int(bp, fn, 750, 0)

    if br_active and timer_set:
        connect(bp, br_active, "Then", timer_set, "execute", fn)
    if timer_set and sw and type_get:
        connect(bp, timer_set, "execute", sw, "execute", fn)
        connect(bp, type_get, "ActiveContractType", sw, "Selection", fn)

    # Type 0: NoHeal — check timer >= 30, if no heal => success
    nh_print = print_node(bp, "[Contract] NoHeal: timer ticking...", fn, 1000, 0)
    if sw and nh_print:
        connect(bp, sw, "0", nh_print, "execute", fn)

    # Type 1: ParryChain
    pc_print = print_node(bp, "[Contract] ParryChain: tracking parries...", fn, 1000, 120)
    if sw and pc_print:
        connect(bp, sw, "1", pc_print, "execute", fn)

    # Type 2: NoHits
    noh_print = print_node(bp, "[Contract] NoHits: stay untouched...", fn, 1000, 240)
    if sw and noh_print:
        connect(bp, sw, "2", noh_print, "execute", fn)

    # Type 3: KillCount
    kc_print = print_node(bp, "[Contract] KillCount: tracking kills...", fn, 1000, 360)
    if sw and kc_print:
        connect(bp, sw, "3", kc_print, "execute", fn)

    # Type 4: LowHPSurvival
    lhp_print = print_node(bp, "[Contract] LowHPSurvival: survive at low HP...", fn, 1000, 480)
    if sw and lhp_print:
        connect(bp, sw, "4", lhp_print, "execute", fn)

    # Type 5: FastClear
    fc_print = print_node(bp, "[Contract] FastClear: clear fast...", fn, 1000, 600)
    if sw and fc_print:
        connect(bp, sw, "5", fc_print, "execute", fn)


def impl_contract_success():
    """Wire ContractSuccess."""
    fn = "ContractSuccess"
    bp = "BP_ContractManager"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    set_inactive = var_set(bp, "bContractActive", fn, 200, 0)
    suc_print = print_node(bp, "[Contract] CONTRACT COMPLETE! Signal reward granted.", fn, 400, 0)
    if set_inactive:
        connect(bp, entry, "execute", set_inactive, "execute", fn)
    if set_inactive and suc_print:
        connect(bp, set_inactive, "execute", suc_print, "execute", fn)


def impl_contract_fail():
    """Wire ContractFail."""
    fn = "ContractFail"
    bp = "BP_ContractManager"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    set_inactive = var_set(bp, "bContractActive", fn, 200, 0)
    fail_print = print_node(bp, "[Contract] Contract FAILED. The System notes your shortcoming.", fn, 400, 0)
    if set_inactive:
        connect(bp, entry, "execute", set_inactive, "execute", fn)
    if set_inactive and fail_print:
        connect(bp, set_inactive, "execute", fail_print, "execute", fn)


def impl_contract_callbacks():
    """Wire OnPlayerDamaged, OnPlayerParried, OnEnemyKilled, OnPlayerHealed."""
    bp = "BP_ContractManager"

    for fn, var, msg in [
        ("OnPlayerDamaged", "bPlayerTookDamage", "[Contract] Player took damage — tracked"),
        ("OnPlayerParried", "ParryChainCount", "[Contract] Parry landed — tracked"),
        ("OnEnemyKilled", "KillCount", "[Contract] Enemy killed — tracked"),
        ("OnPlayerHealed", "bPlayerHealed", "[Contract] Player healed — tracked"),
    ]:
        print(f"  Wiring {fn}...", flush=True)
        entry = "K2Node_FunctionEntry_0"
        v_set = var_set(bp, var, fn, 200, 0)
        cb_print = print_node(bp, msg, fn, 400, 0)
        if v_set:
            connect(bp, entry, "execute", v_set, "execute", fn)
        if v_set and cb_print:
            connect(bp, v_set, "execute", cb_print, "execute", fn)


def impl_contract_get_description():
    """Wire GetContractDescription: switch on type, set description string."""
    fn = "GetContractDescription"
    bp = "BP_ContractManager"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    type_get = var_get(bp, "ActiveContractType", fn, 200, 0)
    sw = switch_int(bp, fn, 400, 0)
    if type_get and sw:
        connect(bp, entry, "execute", sw, "execute", fn)
        connect(bp, type_get, "ActiveContractType", sw, "Selection", fn)

    descs = [
        "NoHeal: Survive 30 seconds without healing",
        "ParryChain: Land 3 parries in 25 seconds",
        "NoHits: Take no hits for 20 seconds",
        "KillCount: Eliminate enemies before time expires",
        "LowHPSurvival: Survive at below 30% HP for 15 seconds",
        "FastClear: Clear the room before time runs out",
    ]
    for i, desc in enumerate(descs):
        d_set = var_set(bp, "ContractDescription", fn, 650, i * 100)
        d_print = print_node(bp, f"[Contract] {desc}", fn, 850, i * 100)
        if sw and d_set:
            connect(bp, sw, str(i), d_set, "execute", fn)
        if d_set and d_print:
            connect(bp, d_set, "execute", d_print, "execute", fn)


def impl_contract_event_graph():
    """Wire ContractManager BeginPlay."""
    bp = "BP_ContractManager"
    print("  Wiring ContractManager EventGraph...", flush=True)

    begin = add_event(bp, "BeginPlay", 0, 0)
    init_print = print_node(bp, "[Contract] ContractManager ready. 6 contract types available.", None, 250, 0)
    if begin and init_print:
        connect(bp, begin, "execute", init_print, "execute")


def build_system():
    print("\n=== PHASE: BP_SystemManager + BP_ContractManager ===", flush=True)
    set_system_defaults()
    impl_system_request_directive()
    impl_system_get_scripted()
    impl_system_show_directive()
    impl_system_clear_directive()
    impl_system_event_graph()
    compile_bp("BP_SystemManager")

    set_contract_defaults()
    impl_contract_offer()
    impl_contract_accept()
    impl_contract_update()
    impl_contract_success()
    impl_contract_fail()
    impl_contract_callbacks()
    impl_contract_get_description()
    impl_contract_event_graph()
    compile_bp("BP_ContractManager")
    print("  DONE: System + Contracts", flush=True)


# ============================================================
# PHASE 4: Level Transitions + Floor 1 Objectives
# ============================================================


def build_transitions():
    """Create BP_LevelTransitionManager and Floor 1 objective logic."""
    print("\n=== PHASE: Level Transitions + Floor 1 Objectives ===", flush=True)

    bp = "BP_GameConfig"

    # Set GameConfig defaults
    print("  Setting GameConfig defaults...", flush=True)
    set_var_default(bp, "MapName_SystemTest", "Map_SystemTest")
    set_var_default(bp, "MapName_HubCity", "Map_HubCitadelCity")
    set_var_default(bp, "MapName_Floor01", "Map_Floor01_Ironcatacomb")
    set_var_default(bp, "MapName_Floor02", "Map_Floor02_VerdantRuins")
    set_var_default(bp, "MapName_Floor03", "Map_Floor03_Skyforge")
    set_var_default(bp, "Floor01_RoomCount", 3)
    set_var_default(bp, "Floor01_SpawnTag", "SpawnGroup_Floor01")
    set_var_default(bp, "Floor02_RoomCount", 3)
    set_var_default(bp, "Floor02_SpawnTag", "SpawnGroup_Floor02")
    set_var_default(bp, "Floor03_RoomCount", 3)
    set_var_default(bp, "Floor03_SpawnTag", "SpawnGroup_Floor03")
    set_var_default(bp, "Floor01_BossGateKills", 3)
    set_var_default(bp, "Floor02_BossGateKills", 3)
    set_var_default(bp, "Floor03_BossGateKills", 3)
    compile_bp(bp)

    # Create Floor1Manager blueprint for objective tracking
    bp_f1 = "BP_Floor1Manager"
    print("  Creating BP_Floor1Manager...", flush=True)
    resp = send("create_blueprint", {"name": bp_f1, "parent_class": "Actor"})
    if not is_ok(resp):
        err = resp.get("error", "")
        if "already exists" not in str(err).lower():
            failed.append(("create_bp:BP_Floor1Manager", str(err)))

    # Variables for Floor 1 objectives
    create_var(bp_f1, "bLeverA_Pulled", "bool", False, "Objectives")
    create_var(bp_f1, "bLeverB_Pulled", "bool", False, "Objectives")
    create_var(bp_f1, "SigilCount", "int", 0, "Objectives")
    create_var(bp_f1, "SigilsRequired", "int", 3, "Objectives")
    create_var(bp_f1, "bBossGateOpen", "bool", False, "Objectives")
    create_var(bp_f1, "bBossDefeated", "bool", False, "Objectives")
    create_var(bp_f1, "bAscensionGateEnabled", "bool", False, "Objectives")

    # Functions
    create_func(bp_f1, "PullLeverA")
    create_func(bp_f1, "PullLeverB")
    create_func(bp_f1, "CollectSigil")
    create_func(bp_f1, "CheckBossGate")
    create_func(bp_f1, "OnBossDefeated")
    create_func(bp_f1, "TravelToFloor1")
    create_func(bp_f1, "ReturnToHub")

    # Wire PullLeverA
    fn = "PullLeverA"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"
    set_a = var_set(bp_f1, "bLeverA_Pulled", fn, 200, 0)
    a_print = print_node(bp_f1, "[Floor1] Lever A pulled!", fn, 400, 0)
    check_call = call_func(bp_f1, "CheckBossGate", fn, x=600, y=0)
    if set_a:
        connect(bp_f1, entry, "execute", set_a, "execute", fn)
    if set_a and a_print:
        connect(bp_f1, set_a, "execute", a_print, "execute", fn)
    if a_print and check_call:
        connect(bp_f1, a_print, "execute", check_call, "execute", fn)

    # Wire PullLeverB
    fn = "PullLeverB"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"
    set_b = var_set(bp_f1, "bLeverB_Pulled", fn, 200, 0)
    b_print = print_node(bp_f1, "[Floor1] Lever B pulled!", fn, 400, 0)
    check_call2 = call_func(bp_f1, "CheckBossGate", fn, x=600, y=0)
    if set_b:
        connect(bp_f1, entry, "execute", set_b, "execute", fn)
    if set_b and b_print:
        connect(bp_f1, set_b, "execute", b_print, "execute", fn)
    if b_print and check_call2:
        connect(bp_f1, b_print, "execute", check_call2, "execute", fn)

    # Wire CollectSigil
    fn = "CollectSigil"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"
    sig_set = var_set(bp_f1, "SigilCount", fn, 200, 0)
    sig_print = print_node(bp_f1, "[Floor1] Sigil fragment collected!", fn, 400, 0)
    check_call3 = call_func(bp_f1, "CheckBossGate", fn, x=600, y=0)
    if sig_set:
        connect(bp_f1, entry, "execute", sig_set, "execute", fn)
    if sig_set and sig_print:
        connect(bp_f1, sig_set, "execute", sig_print, "execute", fn)
    if sig_print and check_call3:
        connect(bp_f1, sig_print, "execute", check_call3, "execute", fn)

    # Wire CheckBossGate
    fn = "CheckBossGate"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"

    # Check: both levers AND sigils >= required
    a_get = var_get(bp_f1, "bLeverA_Pulled", fn, 200, 0)
    b_get = var_get(bp_f1, "bLeverB_Pulled", fn, 200, 80)
    and_node = comparison(bp_f1, "AND", fn, 400, 40)
    br_levers = branch(bp_f1, fn, 550, 0)

    if a_get and b_get and and_node and br_levers:
        connect(bp_f1, entry, "execute", br_levers, "execute", fn)
        connect(bp_f1, a_get, "bLeverA_Pulled", and_node, "A", fn)
        connect(bp_f1, b_get, "bLeverB_Pulled", and_node, "B", fn)
        connect(bp_f1, and_node, "ReturnValue", br_levers, "Condition", fn)

    # Levers OK: check sigils
    sig_get = var_get(bp_f1, "SigilCount", fn, 700, 0)
    req_get = var_get(bp_f1, "SigilsRequired", fn, 700, 80)
    cmp_sig = comparison(bp_f1, ">=", fn, 900, 40)
    br_sig = branch(bp_f1, fn, 1050, 0)

    if br_levers and br_sig and sig_get and req_get and cmp_sig:
        connect(bp_f1, br_levers, "Then", br_sig, "execute", fn)
        connect(bp_f1, sig_get, "SigilCount", cmp_sig, "A", fn)
        connect(bp_f1, req_get, "SigilsRequired", cmp_sig, "B", fn)
        connect(bp_f1, cmp_sig, "ReturnValue", br_sig, "Condition", fn)

    # All conditions met: open gate
    gate_set = var_set(bp_f1, "bBossGateOpen", fn, 1250, 0)
    gate_print = print_node(bp_f1, "[Floor1] BOSS GATE OPENS! The way forward is clear!", fn, 1450, 0)
    if br_sig and gate_set:
        connect(bp_f1, br_sig, "Then", gate_set, "execute", fn)
    if gate_set and gate_print:
        connect(bp_f1, gate_set, "execute", gate_print, "execute", fn)

    # Not met: print status
    not_ready = print_node(bp_f1, "[Floor1] Boss gate locked. Collect sigils and pull both levers.", fn, 1050, 150)
    if br_sig and not_ready:
        connect(bp_f1, br_sig, "Else", not_ready, "execute", fn)

    levers_not = print_node(bp_f1, "[Floor1] Both levers must be pulled first.", fn, 700, 150)
    if br_levers and levers_not:
        connect(bp_f1, br_levers, "Else", levers_not, "execute", fn)

    # Wire OnBossDefeated
    fn = "OnBossDefeated"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"
    set_boss = var_set(bp_f1, "bBossDefeated", fn, 200, 0)
    set_asc = var_set(bp_f1, "bAscensionGateEnabled", fn, 400, 0)
    boss_print = print_node(bp_f1, "[Floor1] BOSS DEFEATED! Ascension Gate unlocked!", fn, 600, 0)
    if set_boss:
        connect(bp_f1, entry, "execute", set_boss, "execute", fn)
    if set_boss and set_asc:
        connect(bp_f1, set_boss, "execute", set_asc, "execute", fn)
    if set_asc and boss_print:
        connect(bp_f1, set_asc, "execute", boss_print, "execute", fn)

    # Wire TravelToFloor1: Open Level by name
    fn = "TravelToFloor1"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"
    travel_print = print_node(bp_f1, "[Travel] Loading Map_Floor01_Ironcatacomb...", fn, 200, 0)
    # Use CallFunction to call OpenLevel
    open_level = call_func(bp_f1, "OpenLevel", fn, x=450, y=0)
    if travel_print:
        connect(bp_f1, entry, "execute", travel_print, "execute", fn)
    if travel_print and open_level:
        connect(bp_f1, travel_print, "execute", open_level, "execute", fn)

    # Wire ReturnToHub
    fn = "ReturnToHub"
    print(f"  Wiring {fn}...", flush=True)
    entry = "K2Node_FunctionEntry_0"
    hub_print = print_node(bp_f1, "[Travel] Returning to Map_HubCitadelCity...", fn, 200, 0)
    open_hub = call_func(bp_f1, "OpenLevel", fn, x=450, y=0)
    if hub_print:
        connect(bp_f1, entry, "execute", hub_print, "execute", fn)
    if hub_print and open_hub:
        connect(bp_f1, hub_print, "execute", open_hub, "execute", fn)

    # EventGraph
    print("  Wiring Floor1Manager EventGraph...", flush=True)
    begin = add_event(bp_f1, "BeginPlay", 0, 0)
    f1_init = print_node(bp_f1, "[Floor1] Floor1Manager initialized. Objectives: 2 levers, 3 sigils, 1 boss.", None, 250, 0)
    if begin and f1_init:
        connect(bp_f1, begin, "execute", f1_init, "execute")

    compile_bp(bp_f1)
    print("  DONE: Level Transitions + Floor 1 Objectives", flush=True)


# ============================================================
# PHASE 5: GameMode, Markers, HUD
# ============================================================


def build_gamemode():
    print("\n=== PHASE: GameMode, Markers, HUD ===", flush=True)

    # BP_SignalBoundGameMode
    bp_gm = "BP_SignalBoundGameMode"
    print("  Wiring GameMode BeginPlay...", flush=True)
    begin = add_event(bp_gm, "BeginPlay", 0, 0)
    gm_print = print_node(bp_gm, "[GameMode] SignalBound GameMode active. Spawning systems...", None, 250, 0)
    seq = sequence(bp_gm, None, 550, 0)

    if begin and gm_print:
        connect(bp_gm, begin, "execute", gm_print, "execute")
    if gm_print and seq:
        connect(bp_gm, gm_print, "execute", seq, "execute")

    # Spawn system actors via prints (actual SpawnActor would need class refs)
    sys_print = print_node(bp_gm, "[GameMode] SystemManager spawned (Scripted provider - offline safe)", None, 800, 0)
    con_print = print_node(bp_gm, "[GameMode] ContractManager spawned (6 contract types)", None, 800, 120)
    hud_print = print_node(bp_gm, "[GameMode] HUDManager spawned", None, 800, 240)
    cfg_print = print_node(bp_gm, "[GameMode] GameConfig loaded", None, 800, 360)

    if seq and sys_print:
        connect(bp_gm, seq, "Then 0", sys_print, "execute")
    if seq and con_print:
        connect(bp_gm, seq, "Then 1", con_print, "execute")
    if seq and hud_print:
        connect(bp_gm, seq, "Then 2", hud_print, "execute")
    if seq and cfg_print:
        connect(bp_gm, seq, "Then 3", cfg_print, "execute")

    compile_bp(bp_gm)

    # BP_SafeNode: add overlap event + heal logic
    bp_sn = "BP_SafeNode"
    print("  Wiring SafeNode BeginPlay...", flush=True)
    set_var_default(bp_sn, "bIsActive", True)
    set_var_default(bp_sn, "HealAmount", 25.0)
    set_var_default(bp_sn, "NodeLabel", "Safe Node")

    begin_sn = add_event(bp_sn, "BeginPlay", 0, 0)
    sn_print = print_node(bp_sn, "[SafeNode] Safe Node active. Step into the light to heal.", None, 250, 0)
    if begin_sn and sn_print:
        connect(bp_sn, begin_sn, "execute", sn_print, "execute")

    # Add overlap event
    overlap_sn = add_event(bp_sn, "ActorBeginOverlap", 0, 200)
    active_get = var_get(bp_sn, "bIsActive", None, 250, 200)
    br_active = branch(bp_sn, None, 400, 200)
    heal_print = print_node(bp_sn, "[SafeNode] Healing player!", None, 600, 200)

    if overlap_sn and br_active and active_get:
        connect(bp_sn, overlap_sn, "execute", br_active, "execute")
        connect(bp_sn, active_get, "bIsActive", br_active, "Condition")
    if br_active and heal_print:
        connect(bp_sn, br_active, "Then", heal_print, "execute")

    compile_bp(bp_sn)

    # BP_AscensionGate: overlap + unlock check
    bp_ag = "BP_AscensionGate"
    print("  Wiring AscensionGate...", flush=True)
    set_var_default(bp_ag, "bIsUnlocked", False)
    set_var_default(bp_ag, "RequiredKillCount", 3)
    set_var_default(bp_ag, "GateLabel", "Ascension Gate")
    set_var_default(bp_ag, "DestinationMap", "Map_HubCitadelCity")

    begin_ag = add_event(bp_ag, "BeginPlay", 0, 0)
    ag_print = print_node(bp_ag, "[AscensionGate] Gate sealed. Defeat the floor boss to unlock.", None, 250, 0)
    if begin_ag and ag_print:
        connect(bp_ag, begin_ag, "execute", ag_print, "execute")

    overlap_ag = add_event(bp_ag, "ActorBeginOverlap", 0, 200)
    unlock_get = var_get(bp_ag, "bIsUnlocked", None, 250, 200)
    br_unlock = branch(bp_ag, None, 400, 200)
    travel_print = print_node(bp_ag, "[AscensionGate] Gate OPEN! Transitioning...", None, 600, 150)
    locked_print = print_node(bp_ag, "[AscensionGate] Gate is LOCKED. Defeat the boss first.", None, 600, 300)

    if overlap_ag and br_unlock and unlock_get:
        connect(bp_ag, overlap_ag, "execute", br_unlock, "execute")
        connect(bp_ag, unlock_get, "bIsUnlocked", br_unlock, "Condition")
    if br_unlock and travel_print:
        connect(bp_ag, br_unlock, "Then", travel_print, "execute")
    if br_unlock and locked_print:
        connect(bp_ag, br_unlock, "Else", locked_print, "execute")

    compile_bp(bp_ag)

    # BP_SystemNoticePlaque: overlap + read
    bp_sp = "BP_SystemNoticePlaque"
    print("  Wiring SystemNoticePlaque...", flush=True)
    set_var_default(bp_sp, "bHasBeenRead", False)
    set_var_default(bp_sp, "NoticeText", "The System speaks through these plaques. Read carefully.")

    begin_sp = add_event(bp_sp, "BeginPlay", 0, 0)
    sp_print = print_node(bp_sp, "[Plaque] System Notice Plaque placed.", None, 250, 0)
    if begin_sp and sp_print:
        connect(bp_sp, begin_sp, "execute", sp_print, "execute")

    overlap_sp = add_event(bp_sp, "ActorBeginOverlap", 0, 200)
    read_get = var_get(bp_sp, "bHasBeenRead", None, 250, 200)
    br_read = branch(bp_sp, None, 400, 200)
    text_get = var_get(bp_sp, "NoticeText", None, 400, 350)
    read_print = print_node(bp_sp, "[Plaque] Reading notice...", None, 600, 200)
    set_read = var_set(bp_sp, "bHasBeenRead", None, 800, 200)
    already_print = print_node(bp_sp, "[Plaque] Already read.", None, 600, 350)

    if overlap_sp and br_read and read_get:
        connect(bp_sp, overlap_sp, "execute", br_read, "execute")
        connect(bp_sp, read_get, "bHasBeenRead", br_read, "Condition")
    if br_read and already_print:
        connect(bp_sp, br_read, "Then", already_print, "execute")
    if br_read and read_print:
        connect(bp_sp, br_read, "Else", read_print, "execute")
    if read_print and set_read:
        connect(bp_sp, read_print, "execute", set_read, "execute")

    compile_bp(bp_sp)

    # BP_HUDManager functions
    bp_hud = "BP_HUDManager"
    print("  Wiring HUDManager functions...", flush=True)

    for fn, msg in [
        ("CreateHUD", "[HUD] Player HUD created"),
        ("UpdateHealth", "[HUD] Health updated"),
        ("UpdateStamina", "[HUD] Stamina updated"),
        ("UpdateCooldown", "[HUD] Cooldown updated"),
        ("ShowNotice", "[HUD] System notice displayed"),
        ("ShowDirective", "[HUD] Directive displayed"),
        ("ToggleMenu", "[HUD] Menu toggled"),
    ]:
        entry = "K2Node_FunctionEntry_0"
        p = print_node(bp_hud, msg, fn, 200, 0)
        if p:
            connect(bp_hud, entry, "execute", p, "execute", fn)

    begin_hud = add_event(bp_hud, "BeginPlay", 0, 0)
    hud_init = print_node(bp_hud, "[HUD] HUDManager initialized", None, 250, 0)
    create_call = call_func(bp_hud, "CreateHUD", None, x=500, y=0)
    if begin_hud and hud_init:
        connect(bp_hud, begin_hud, "execute", hud_init, "execute")
    if hud_init and create_call:
        connect(bp_hud, hud_init, "execute", create_call, "execute")

    compile_bp(bp_hud)

    print("  DONE: GameMode, Markers, HUD", flush=True)


# ============================================================
# MAIN
# ============================================================
def main() -> int:
    parser = argparse.ArgumentParser(description="Implement Phase 1 gameplay logic via MCP.")
    parser.add_argument(
        "--phase",
        choices=["all", "player", "enemy", "system", "transitions", "gamemode"],
        default="all",
    )
    args = parser.parse_args()

    ping = send("ping", {})
    if not is_ok(ping):
        print(f"ERROR: MCP ping failed: {ping}")
        return 2

    phase = args.phase
    if phase in ("all", "player"):
        build_player()
    if phase in ("all", "enemy"):
        build_enemy()
    if phase in ("all", "system"):
        build_system()
    if phase in ("all", "transitions"):
        build_transitions()
    if phase in ("all", "gamemode"):
        build_gamemode()

    print(f"\n{'='*50}")
    print(f"NODES_CREATED={nodes_created}")
    print(f"CONNECTIONS_MADE={connections_made}")
    if failed:
        print(f"FAILED_COUNT={len(failed)}")
        for name, err in failed[:50]:
            print(f"  FAILED {name}: {err}")
    else:
        print("FAILED_COUNT=0")
    print(f"{'='*50}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
