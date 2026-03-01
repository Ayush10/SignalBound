#!/usr/bin/env python3
"""Final fix: Re-add missing CallFunction nodes and reconnect all exec chains."""
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
    print(f"  FAIL: {label} — {err[:120]}")
    return False

def conn(bp, src, spin, tgt, tpin):
    if not src or not tgt:
        print(f"  SKIP conn: missing id ({spin}→{tpin})")
        return False
    return ok(mcp("connect_nodes", {"blueprint_name": bp, "source_node_id": src, "source_pin_name": spin, "target_node_id": tgt, "target_pin_name": tpin}), f"conn({spin}→{tpin})")

def node(bp, ntype, params):
    r = mcp("add_blueprint_node", {"blueprint_name": bp, "node_type": ntype, "node_params": params})
    i = nid(r)
    ok(r, f"node({ntype})→{i[:24]}")
    return i

def call_func(bp, func_name, pos_x=0, pos_y=0):
    """Add CallFunction node for a custom BP function."""
    cls = f"/Game/Blueprints/{bp}.{bp}_C"
    r = mcp("add_blueprint_node", {"blueprint_name": bp, "node_type": "CallFunction", "node_params": {
        "target_function": func_name,
        "target_class": cls,
        "pos_x": pos_x, "pos_y": pos_y
    }})
    i = nid(r)
    ok(r, f"CallFunction({func_name})→{i[:24]}")
    return i

def get_nodes(bp):
    r = mcp("analyze_blueprint_graph", {"blueprint_path": f"/Game/Blueprints/{bp}"})
    if r and r.get("status") == "success":
        return r["result"]["graph_data"]["nodes"]
    return []

def compile_bp(bp):
    ok(mcp("compile_blueprint", {"blueprint_name": bp}), f"compile({bp})")


print("=== Final Fix: Missing CallFunction nodes + Exec chains ===\n")
r = mcp("ping")
if not r or r.get("status") != "success":
    print("MCP not reachable"); sys.exit(1)


# ─── BP_EnemyBase ───
# Current state: Tick→IfThenElse_1(connected), IfThenElse_1.else needs → TickStateMachine
# K2Node_CallFunction_9 exists but is disconnected
print("--- BP_EnemyBase: Connect Branch.else → TickStateMachine ---")
conn("BP_EnemyBase", "K2Node_IfThenElse_1", "else", "K2Node_CallFunction_9", "execute")
# Also connect BeginPlay → first Print
conn("BP_EnemyBase", "K2Node_Event_0", "then", "K2Node_CallFunction_2", "execute")
compile_bp("BP_EnemyBase")


# ─── BP_PlayerCharacter ───
# Need: Tick → UpdateStaminaRegen → UpdateSwordSkillCooldown → UpdateHUDValues
# CallFunction nodes are missing — re-add them
print("\n--- BP_PlayerCharacter: Add + connect Tick chain ---")
n1 = call_func("BP_PlayerCharacter", "UpdateStaminaRegen", 300, 250)
n2 = call_func("BP_PlayerCharacter", "UpdateSwordSkillCooldown", 600, 250)
n3 = call_func("BP_PlayerCharacter", "UpdateHUDValues", 900, 250)

conn("BP_PlayerCharacter", "K2Node_Event_2", "then", n1, "execute")
if n1 and n2:
    conn("BP_PlayerCharacter", n1, "then", n2, "execute")
if n2 and n3:
    conn("BP_PlayerCharacter", n2, "then", n3, "execute")
compile_bp("BP_PlayerCharacter")


# ─── BP_SystemManager ───
# Need: BeginPlay → RequestDirective → Print
print("\n--- BP_SystemManager: Add + connect BeginPlay chain ---")
n_rd = call_func("BP_SystemManager", "RequestDirective", 300, 0)
conn("BP_SystemManager", "K2Node_Event_0", "then", n_rd, "execute")
if n_rd:
    conn("BP_SystemManager", n_rd, "then", "K2Node_CallFunction_3", "execute")
compile_bp("BP_SystemManager")


# ─── BP_ContractManager ───
# Need: Tick → Branch(bContractActive) → UpdateContract
# Branch is connected to Tick now. Need UpdateContract CallFunction
print("\n--- BP_ContractManager: Add UpdateContract ---")
n_uc = call_func("BP_ContractManager", "UpdateContract", 600, 0)
# IfThenElse_1 is connected to Tick
conn("BP_ContractManager", "K2Node_IfThenElse_1", "then", n_uc, "execute")
compile_bp("BP_ContractManager")


# ─── BP_HUDManager ───
# Need: BeginPlay → CreateHUD → Print
print("\n--- BP_HUDManager: Add + connect BeginPlay chain ---")
n_ch = call_func("BP_HUDManager", "CreateHUD", 300, 0)
conn("BP_HUDManager", "K2Node_Event_0", "then", n_ch, "execute")
if n_ch:
    conn("BP_HUDManager", n_ch, "then", "K2Node_CallFunction_3", "execute")
compile_bp("BP_HUDManager")


# ─── BP_SystemNoticePlaque ───
# Need: Overlap → Branch(bHasBeenRead check) → Print → Set(bHasBeenRead)
# The branch with bHasBeenRead condition needs to be found
print("\n--- BP_SystemNoticePlaque: Fix overlap chain ---")
nodes = get_nodes("BP_SystemNoticePlaque")
overlap = None
branch_read = None
for n in nodes:
    t = n.get("title","")
    if "ActorBeginOverlap" in t:
        overlap = n["name"]
    elif "Branch" in t:
        # Check if this branch has condition connected (to bHasBeenRead)
        for p in n.get("pins",[]):
            if p.get("name") == "Condition" and p.get("connections",0) > 0:
                branch_read = n["name"]

print(f"  overlap={overlap}, branch_read={branch_read}")

# If no branch has condition connected, connect bHasBeenRead to the first available branch
if not branch_read:
    # Find a branch and connect bHasBeenRead variable to it
    branches = [n["name"] for n in nodes if "Branch" in n.get("title","")]
    var_read = None
    for n in nodes:
        if "bHasBeenRead" in n.get("title","") and "Get" in n.get("title",""):
            var_read = n["name"]

    if not var_read:
        # Add a VariableGet for bHasBeenRead
        r = mcp("add_blueprint_node", {"blueprint_name": "BP_SystemNoticePlaque", "node_type": "VariableGet", "node_params": {"variable_name": "bHasBeenRead", "pos_x": 200, "pos_y": 50}})
        var_read = nid(r)
        ok(r, f"VariableGet(bHasBeenRead)→{var_read[:20]}")

    if branches and var_read:
        branch_read = branches[0]
        conn("BP_SystemNoticePlaque", var_read, "bHasBeenRead", branch_read, "Condition")

if overlap and branch_read:
    conn("BP_SystemNoticePlaque", overlap, "then", branch_read, "execute")

# Branch else (NOT read) → Print → Set
print_n = None
set_n = None
for n in nodes:
    if "Print String" in n.get("title",""):
        print_n = n["name"]
    elif "Set" in n.get("title","") and "VariableSet" in n["name"]:
        set_n = n["name"]

if branch_read and print_n:
    conn("BP_SystemNoticePlaque", branch_read, "else", print_n, "execute")
if print_n and set_n:
    conn("BP_SystemNoticePlaque", print_n, "then", set_n, "execute")

compile_bp("BP_SystemNoticePlaque")


# ─── Final verification ───
print("\n=== Final Verification ===")
ALL_BPS = [
    'BP_SafeNode', 'BP_AscensionGate', 'BP_SystemNoticePlaque',
    'BP_GameConfig', 'BP_EnemyBase',
    'BP_PlayerCharacter', 'BP_SystemManager', 'BP_ContractManager',
    'BP_HUDManager', 'BP_SignalBoundGameMode'
]

for bp in ALL_BPS:
    r = mcp("compile_blueprint", {"blueprint_name": bp})
    compiled = r and r.get("status") == "success"

    r = mcp("analyze_blueprint_graph", {"blueprint_path": f"/Game/Blueprints/{bp}"})
    if r and r.get("status") == "success":
        nodes = r["result"]["graph_data"]["nodes"]
        total_exec = sum(
            sum(1 for p in n.get("pins",[]) if p.get("type") == "exec" and p.get("connections",0) > 0)
            for n in nodes
        )
        disconnected = []
        for n in nodes:
            if "Event" in n.get("title",""):
                has_out = any(p.get("connections",0) > 0 for p in n.get("pins",[]) if p.get("name") == "then")
                if not has_out and "Overlap" not in n.get("title","") and "Tick" not in n.get("title",""):
                    disconnected.append(n.get("title",""))
        status = "PASS" if compiled else "FAIL"
        warn = f" ⚠ disconnected: {disconnected}" if disconnected else ""
        print(f"  {bp}: {status} | {len(nodes)} nodes, {total_exec} exec conns{warn}")
    else:
        print(f"  {bp}: {'PASS' if compiled else 'FAIL'} | graph unavailable")

print("\n=== Done! ===")
