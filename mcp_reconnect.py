#!/usr/bin/env python3
"""Reconnect all exec chains across all Phase 1 blueprints."""
import socket, json, sys

HOST = '127.0.0.1'
PORT = 55557

def mcp(cmd_type, params=None, timeout=30):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4194304)
    sock.connect((HOST, PORT))
    sock.sendall(json.dumps({"type": cmd_type, "params": params or {}}).encode('utf-8'))
    chunks = []
    while True:
        try:
            chunk = sock.recv(262144)
            if not chunk: break
            chunks.append(chunk)
            try: return json.loads(b''.join(chunks).decode('utf-8'))
            except: continue
        except: break
    sock.close()
    return {"status":"error","error":"timeout"}

def nid(resp):
    r = resp.get("result", resp)
    return r.get("node_id","") if isinstance(r, dict) else ""

def ok(resp, label=""):
    status = resp.get("status","")
    result = resp.get("result",{})
    success = (status == "success") or resp.get("success", False) or (isinstance(result, dict) and result.get("success", False))
    if success:
        print(f"  OK: {label}")
        return True
    err = resp.get("error","") or (result.get("error","") if isinstance(result, dict) else "")
    print(f"  FAIL: {label} — {err[:100]}")
    return False

def conn(bp, src, spin, tgt, tpin):
    if not src or not tgt:
        print(f"  SKIP: missing id for conn({spin}→{tpin})")
        return False
    return ok(mcp("connect_nodes", {"blueprint_name": bp, "source_node_id": src, "source_pin_name": spin, "target_node_id": tgt, "target_pin_name": tpin}), f"conn({src[:12]}:{spin} → {tgt[:12]}:{tpin})")

def node(bp, ntype, params):
    r = mcp("add_blueprint_node", {"blueprint_name": bp, "node_type": ntype, "node_params": params})
    i = nid(r)
    ok(r, f"node({ntype})→{i[:20]}")
    return i

def get_nodes(bp):
    r = mcp("analyze_blueprint_graph", {"blueprint_path": f"/Game/Blueprints/{bp}"})
    if r and r.get("status") == "success":
        return r["result"]["graph_data"]["nodes"]
    return []

def find(nodes, key, value):
    """Find first node where key field contains value."""
    for n in nodes:
        if value in str(n.get(key, "")):
            return n["name"]
    return None

def find_all(nodes, key, value):
    """Find all nodes where key field contains value."""
    return [n["name"] for n in nodes if value in str(n.get(key, ""))]

def compile_bp(bp):
    ok(mcp("compile_blueprint", {"blueprint_name": bp}), f"compile({bp})")


print("=== Reconnecting all Phase 1 exec chains ===\n")
r = mcp("ping")
if not r or r.get("status") != "success":
    print("MCP not reachable"); sys.exit(1)

BP = "/Game/Blueprints"

# ─── BP_SafeNode ───
# BeginPlay → Print(NodeLabel)
# Overlap → Branch(bIsActive) → Print("Safe Node Activated")
print("--- BP_SafeNode ---")
nodes = get_nodes("BP_SafeNode")
bp_event = find(nodes, "title", "BeginPlay")
overlap_event = find(nodes, "title", "ActorBeginOverlap")
# Branch connected to bIsActive
branch_bIsActive = None
for n in nodes:
    if "Branch" in n.get("title",""):
        for p in n.get("pins",[]):
            if p.get("name") == "Condition" and p.get("connections",0) > 0:
                branch_bIsActive = n["name"]
                break

# The other branch is unused (IfThenElse_0)
# Print nodes
print_nodes = find_all(nodes, "title", "Print String")
print(f"  bp={bp_event}, overlap={overlap_event}, branch_active={branch_bIsActive}, prints={print_nodes}")

# BeginPlay → first Print (already connected)
# Overlap → Branch(bIsActive)
if overlap_event and branch_bIsActive:
    conn("BP_SafeNode", overlap_event, "then", branch_bIsActive, "execute")
# Branch(then=active) → second Print
if branch_bIsActive and len(print_nodes) > 1:
    conn("BP_SafeNode", branch_bIsActive, "then", print_nodes[1], "execute")
compile_bp("BP_SafeNode")


# ─── BP_AscensionGate ───
# Overlap → Branch(bIsUnlocked) → Print("Gate Open")
print("\n--- BP_AscensionGate ---")
nodes = get_nodes("BP_AscensionGate")
overlap = find(nodes, "title", "ActorBeginOverlap")
# Find branch connected to bIsUnlocked
branch_unlocked = None
for n in nodes:
    if "Branch" in n.get("title",""):
        for p in n.get("pins",[]):
            if p.get("name") == "Condition" and p.get("connections",0) > 0:
                branch_unlocked = n["name"]
                break
print_n = find(nodes, "title", "Print String")
print(f"  overlap={overlap}, branch={branch_unlocked}, print={print_n}")

if overlap and branch_unlocked:
    conn("BP_AscensionGate", overlap, "then", branch_unlocked, "execute")
if branch_unlocked and print_n:
    conn("BP_AscensionGate", branch_unlocked, "then", print_n, "execute")
compile_bp("BP_AscensionGate")


# ─── BP_SystemNoticePlaque ───
# Overlap → Branch(NOT bHasBeenRead) → Print(NoticeText) → Set(bHasBeenRead=true)
print("\n--- BP_SystemNoticePlaque ---")
nodes = get_nodes("BP_SystemNoticePlaque")
overlap = find(nodes, "title", "ActorBeginOverlap")
# Find branch with condition connected
branch_n = None
for n in nodes:
    if "Branch" in n.get("title",""):
        for p in n.get("pins",[]):
            if p.get("name") == "Condition" and p.get("connections",0) > 0:
                branch_n = n["name"]
                break
print_n = find(nodes, "title", "Print String")
set_n = find(nodes, "title", "Set")
print(f"  overlap={overlap}, branch={branch_n}, print={print_n}, set={set_n}")

if overlap and branch_n:
    conn("BP_SystemNoticePlaque", overlap, "then", branch_n, "execute")
# Branch else = NOT read (we want action when bHasBeenRead is false)
if branch_n and print_n:
    conn("BP_SystemNoticePlaque", branch_n, "else", print_n, "execute")
# We need a Set node for bHasBeenRead
if not set_n:
    set_n = node("BP_SystemNoticePlaque", "VariableSet", {"variable_name": "bHasBeenRead", "pos_x": 700, "pos_y": 0})
if print_n and set_n:
    conn("BP_SystemNoticePlaque", print_n, "then", set_n, "execute")
compile_bp("BP_SystemNoticePlaque")


# ─── BP_EnemyBase ───
# BeginPlay → Print("Enemy Spawned")
# Tick → Branch(NOT bIsDead) (else) → CallFunction(TickStateMachine)
print("\n--- BP_EnemyBase ---")
nodes = get_nodes("BP_EnemyBase")
bp_event = find(nodes, "title", "BeginPlay")
tick_event = find(nodes, "title", "Tick")
prints = find_all(nodes, "title", "Print String")
branches = find_all(nodes, "title", "Branch")
call_funcs = find_all(nodes, "title", "TickStateMachine")
if not call_funcs:
    call_funcs = [n["name"] for n in nodes if "CallFunction" in n["name"] and n["name"] not in prints]

# Find TickStateMachine CallFunction
tick_sm = None
for n in nodes:
    t = n.get("title","")
    if "TickStateMachine" in t or ("CallFunction" in n["name"] and n["name"] not in prints):
        # Check if it's the one we added for TickStateMachine
        tick_sm = n["name"]

# Find the Branch connected to bIsDead
branch_dead = None
for n in nodes:
    if "Branch" in n.get("title",""):
        for p in n.get("pins",[]):
            if p.get("name") == "Condition" and p.get("connections", 0) > 0:
                branch_dead = n["name"]
                break

print(f"  bp={bp_event}, tick={tick_event}, branch_dead={branch_dead}, prints={prints}")

# Already connected: BeginPlay→Print, Tick→Branch
# Need: Branch(else=alive)→TickStateMachine
# Check which nodes already have exec connections
for n in nodes:
    exec_out = sum(1 for p in n.get("pins",[]) if p.get("type") == "exec" and p.get("direction","") == "Output" and p.get("connections",0) > 0)
    exec_in = sum(1 for p in n.get("pins",[]) if p.get("type") == "exec" and p.get("direction","") == "Input" and p.get("connections",0) > 0)
    if exec_out > 0 or exec_in > 0:
        print(f"    {n['name']} [{n.get('title','')}] exec_in={exec_in} exec_out={exec_out}")
compile_bp("BP_EnemyBase")


# ─── BP_PlayerCharacter ───
# BeginPlay → Print
# Tick → UpdateStaminaRegen → UpdateSwordSkillCooldown → UpdateHUDValues
print("\n--- BP_PlayerCharacter ---")
nodes = get_nodes("BP_PlayerCharacter")
bp_event = find(nodes, "title", "BeginPlay")
tick_event = find(nodes, "title", "Tick")
prints = find_all(nodes, "title", "Print String")
call_funcs = [n for n in nodes if "CallFunction" in n["name"]]

print(f"  bp={bp_event}, tick={tick_event}, call_funcs={len(call_funcs)}")
for n in nodes:
    exec_out = sum(1 for p in n.get("pins",[]) if p.get("type") == "exec" and p.get("direction","") == "Output" and p.get("connections",0) > 0)
    exec_in = sum(1 for p in n.get("pins",[]) if p.get("type") == "exec" and p.get("direction","") == "Input" and p.get("connections",0) > 0)
    if exec_out > 0 or exec_in > 0:
        print(f"    {n['name']} [{n.get('title','')}] exec_in={exec_in} exec_out={exec_out}")
compile_bp("BP_PlayerCharacter")


# ─── BP_SystemManager ───
# BeginPlay → RequestDirective → Print
print("\n--- BP_SystemManager ---")
nodes = get_nodes("BP_SystemManager")
bp_event = find(nodes, "title", "BeginPlay")
call_funcs = [n for n in nodes if "CallFunction" in n["name"]]
prints = find_all(nodes, "title", "Print String")
print(f"  bp={bp_event}, call_funcs={len(call_funcs)}, prints={prints}")
for n in nodes:
    exec_out = sum(1 for p in n.get("pins",[]) if p.get("type") == "exec" and p.get("direction","") == "Output" and p.get("connections",0) > 0)
    exec_in = sum(1 for p in n.get("pins",[]) if p.get("type") == "exec" and p.get("direction","") == "Input" and p.get("connections",0) > 0)
    if exec_out > 0 or exec_in > 0:
        print(f"    {n['name']} [{n.get('title','')}] exec_in={exec_in} exec_out={exec_out}")

# Try connecting: bp→first_call_func→print
# The RequestDirective CallFunction should already exist from mcp_fix.py
if call_funcs:
    # Find which CallFunction is RequestDirective (not PrintString)
    req_dir = None
    for cf in call_funcs:
        if cf["name"] not in prints and "Print" not in cf.get("title",""):
            req_dir = cf["name"]
            break
    print(f"  RequestDirective node: {req_dir}")
    if bp_event and req_dir:
        conn("BP_SystemManager", bp_event, "then", req_dir, "execute")
    if req_dir and prints:
        conn("BP_SystemManager", req_dir, "then", prints[0], "execute")
compile_bp("BP_SystemManager")


# ─── BP_ContractManager ───
# Tick → Branch(bContractActive) → UpdateContract
print("\n--- BP_ContractManager ---")
nodes = get_nodes("BP_ContractManager")
tick = find(nodes, "title", "Tick")
branches = find_all(nodes, "title", "Branch")
call_funcs = [n for n in nodes if "CallFunction" in n["name"]]
print(f"  tick={tick}, branches={branches}, call_funcs={len(call_funcs)}")

# Find branch with condition connected
branch_active = None
for n in nodes:
    if "Branch" in n.get("title",""):
        for p in n.get("pins",[]):
            if p.get("name") == "Condition" and p.get("connections", 0) > 0:
                branch_active = n["name"]
                break

# Find UpdateContract CallFunction
update_contract = None
for cf in call_funcs:
    if "Print" not in cf.get("title",""):
        update_contract = cf["name"]
        break

print(f"  branch_active={branch_active}, update_contract={update_contract}")
if tick and branch_active:
    conn("BP_ContractManager", tick, "then", branch_active, "execute")
if branch_active and update_contract:
    conn("BP_ContractManager", branch_active, "then", update_contract, "execute")
compile_bp("BP_ContractManager")


# ─── BP_HUDManager ───
# BeginPlay → CreateHUD → Print
print("\n--- BP_HUDManager ---")
nodes = get_nodes("BP_HUDManager")
bp_event = find(nodes, "title", "BeginPlay")
prints = find_all(nodes, "title", "Print String")
call_funcs = [n for n in nodes if "CallFunction" in n["name"]]

create_hud = None
for cf in call_funcs:
    if cf["name"] not in prints and "Print" not in cf.get("title",""):
        create_hud = cf["name"]
        break

print(f"  bp={bp_event}, create_hud={create_hud}, prints={prints}")
if bp_event and create_hud:
    conn("BP_HUDManager", bp_event, "then", create_hud, "execute")
if create_hud and prints:
    conn("BP_HUDManager", create_hud, "then", prints[0], "execute")
compile_bp("BP_HUDManager")


# ─── BP_SignalBoundGameMode ───
# Already has BeginPlay → Print connected
print("\n--- BP_SignalBoundGameMode ---")
nodes = get_nodes("BP_SignalBoundGameMode")
for n in nodes:
    exec_out = sum(1 for p in n.get("pins",[]) if p.get("type") == "exec" and p.get("direction","") == "Output" and p.get("connections",0) > 0)
    exec_in = sum(1 for p in n.get("pins",[]) if p.get("type") == "exec" and p.get("direction","") == "Input" and p.get("connections",0) > 0)
    print(f"  {n['name']} [{n.get('title','')}] exec_in={exec_in} exec_out={exec_out}")
compile_bp("BP_SignalBoundGameMode")


print("\n=== Reconnection complete! ===")
