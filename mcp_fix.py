#!/usr/bin/env python3
"""Fix script: Add missing CallFunction nodes for custom BP functions and connect them."""
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
    print(f"  FAIL: {label} — {err[:80]}")
    return False

def node(bp, ntype, params):
    r = mcp("add_blueprint_node", {"blueprint_name": bp, "node_type": ntype, "node_params": params})
    i = nid(r)
    ok(r, f"node({ntype})→{i[:16]}")
    return i

def conn(bp, src, spin, tgt, tpin):
    if not src or not tgt:
        print(f"  SKIP: missing id")
        return False
    return ok(mcp("connect_nodes", {"blueprint_name": bp, "source_node_id": src, "source_pin_name": spin, "target_node_id": tgt, "target_pin_name": tpin}), f"conn({spin}→{tpin})")

BP = "/Game/Blueprints"

def self_class(bp_name):
    return f"{BP}/{bp_name}.{bp_name}_C"


print("=== Fix: Adding custom function CallFunction nodes ===\n")
r = mcp("ping")
if not r or r.get("status") != "success":
    print("MCP not reachable"); sys.exit(1)

# ── BP_EnemyBase: Tick → Branch(else=!dead) → TickStateMachine ──
print("--- BP_EnemyBase: Tick → TickStateMachine ---")
# The Branch node already exists and is connected to Tick. We just need to add the CallFunction for TickStateMachine
# First, get current graph state to find the Branch node ID
r = mcp("analyze_blueprint_graph", {"blueprint_path": f"{BP}/BP_EnemyBase"})
if r and r.get("status") == "success":
    nodes = r["result"]["graph_data"]["nodes"]
    # Find the branch that's connected to bIsDead
    branch_id = None
    tick_event_id = None
    for n in nodes:
        if "Branch" in n.get("title","") and any(p.get("name") == "Condition" and p.get("connections",0) > 0 for p in n.get("pins",[])):
            # This is the branch connected to bIsDead (from our previous run)
            if not branch_id:  # Take first one that might be for dead check
                branch_id = n["name"]
        if "Tick" in n.get("title",""):
            tick_event_id = n["name"]

    print(f"  Found branch: {branch_id}, tick: {tick_event_id}")

    # Add the custom function call
    n_tsm = node("BP_EnemyBase", "CallFunction", {
        "target_function": "TickStateMachine",
        "target_class": self_class("BP_EnemyBase"),
        "pos_x": 700, "pos_y": 300
    })
    if branch_id and n_tsm:
        conn("BP_EnemyBase", branch_id, "else", n_tsm, "execute")

    ok(mcp("compile_blueprint", {"blueprint_name": "BP_EnemyBase"}), "compile(BP_EnemyBase)")

# ── BP_PlayerCharacter: Tick → UpdateStaminaRegen → UpdateSwordSkillCooldown → UpdateHUDValues ──
print("\n--- BP_PlayerCharacter: Tick chain ---")
r = mcp("analyze_blueprint_graph", {"blueprint_path": f"{BP}/BP_PlayerCharacter"})
if r and r.get("status") == "success":
    nodes = r["result"]["graph_data"]["nodes"]
    tick_id = None
    for n in nodes:
        if "Tick" in n.get("title",""):
            tick_id = n["name"]
    print(f"  Found tick: {tick_id}")

    cls = self_class("BP_PlayerCharacter")
    n1 = node("BP_PlayerCharacter", "CallFunction", {"target_function": "UpdateStaminaRegen", "target_class": cls, "pos_x": 300, "pos_y": 250})
    n2 = node("BP_PlayerCharacter", "CallFunction", {"target_function": "UpdateSwordSkillCooldown", "target_class": cls, "pos_x": 550, "pos_y": 250})
    n3 = node("BP_PlayerCharacter", "CallFunction", {"target_function": "UpdateHUDValues", "target_class": cls, "pos_x": 800, "pos_y": 250})

    if tick_id and n1:
        conn("BP_PlayerCharacter", tick_id, "then", n1, "execute")
    if n1 and n2:
        conn("BP_PlayerCharacter", n1, "then", n2, "execute")
    if n2 and n3:
        conn("BP_PlayerCharacter", n2, "then", n3, "execute")

    ok(mcp("compile_blueprint", {"blueprint_name": "BP_PlayerCharacter"}), "compile(BP_PlayerCharacter)")

# ── BP_SystemManager: BeginPlay → RequestDirective → Print ──
print("\n--- BP_SystemManager: BeginPlay → RequestDirective ---")
r = mcp("analyze_blueprint_graph", {"blueprint_path": f"{BP}/BP_SystemManager"})
if r and r.get("status") == "success":
    nodes = r["result"]["graph_data"]["nodes"]
    bp_id = None
    print_id = None
    for n in nodes:
        if "BeginPlay" in n.get("title",""):
            bp_id = n["name"]
        if "Print String" in n.get("title",""):
            print_id = n["name"]
    print(f"  Found beginplay: {bp_id}, print: {print_id}")

    n1 = node("BP_SystemManager", "CallFunction", {
        "target_function": "RequestDirective",
        "target_class": self_class("BP_SystemManager"),
        "pos_x": 300, "pos_y": 0
    })
    if bp_id and n1:
        conn("BP_SystemManager", bp_id, "then", n1, "execute")
    if n1 and print_id:
        conn("BP_SystemManager", n1, "then", print_id, "execute")

    ok(mcp("compile_blueprint", {"blueprint_name": "BP_SystemManager"}), "compile(BP_SystemManager)")

# ── BP_ContractManager: Tick → Branch → UpdateContract ──
print("\n--- BP_ContractManager: Branch → UpdateContract ---")
r = mcp("analyze_blueprint_graph", {"blueprint_path": f"{BP}/BP_ContractManager"})
if r and r.get("status") == "success":
    nodes = r["result"]["graph_data"]["nodes"]
    branch_id = None
    for n in nodes:
        if "Branch" in n.get("title",""):
            branch_id = n["name"]
    print(f"  Found branch: {branch_id}")

    n1 = node("BP_ContractManager", "CallFunction", {
        "target_function": "UpdateContract",
        "target_class": self_class("BP_ContractManager"),
        "pos_x": 600, "pos_y": 0
    })
    if branch_id and n1:
        conn("BP_ContractManager", branch_id, "then", n1, "execute")

    ok(mcp("compile_blueprint", {"blueprint_name": "BP_ContractManager"}), "compile(BP_ContractManager)")

# ── BP_HUDManager: BeginPlay → CreateHUD → Print ──
print("\n--- BP_HUDManager: BeginPlay → CreateHUD ---")
r = mcp("analyze_blueprint_graph", {"blueprint_path": f"{BP}/BP_HUDManager"})
if r and r.get("status") == "success":
    nodes = r["result"]["graph_data"]["nodes"]
    bp_id = None
    print_id = None
    for n in nodes:
        if "BeginPlay" in n.get("title",""):
            bp_id = n["name"]
        if "Print String" in n.get("title",""):
            print_id = n["name"]
    print(f"  Found beginplay: {bp_id}, print: {print_id}")

    n1 = node("BP_HUDManager", "CallFunction", {
        "target_function": "CreateHUD",
        "target_class": self_class("BP_HUDManager"),
        "pos_x": 300, "pos_y": 0
    })
    if bp_id and n1:
        conn("BP_HUDManager", bp_id, "then", n1, "execute")
    if n1 and print_id:
        conn("BP_HUDManager", n1, "then", print_id, "execute")

    ok(mcp("compile_blueprint", {"blueprint_name": "BP_HUDManager"}), "compile(BP_HUDManager)")

# ── Fix BP_SafeNode connections too ──
print("\n--- BP_SafeNode: Fix exec connections ---")
r = mcp("analyze_blueprint_graph", {"blueprint_path": f"{BP}/BP_SafeNode"})
if r and r.get("status") == "success":
    nodes = r["result"]["graph_data"]["nodes"]
    for n in nodes:
        name = n["name"]
        title = n.get("title","")
        conns = sum(p.get("connections",0) for p in n.get("pins",[]) if p.get("type") == "exec")
        print(f"  {name} [{title}] exec_conns={conns}")

    # Find BeginPlay and its PrintString
    bp_event = None
    overlap_event = None
    print_nodes = []
    branch_nodes = []
    for n in nodes:
        if "BeginPlay" in n.get("title",""):
            bp_event = n["name"]
        elif "ActorBeginOverlap" in n.get("title",""):
            overlap_event = n["name"]
        elif "Print String" in n.get("title",""):
            print_nodes.append(n["name"])
        elif "Branch" in n.get("title",""):
            branch_nodes.append(n["name"])

    # BeginPlay already connected from earlier fix run. Check overlap→branch→print
    if overlap_event and branch_nodes:
        conn("BP_SafeNode", overlap_event, "then", branch_nodes[0], "execute")
    if len(branch_nodes) > 0 and len(print_nodes) > 1:
        conn("BP_SafeNode", branch_nodes[0], "then", print_nodes[1], "execute")

    ok(mcp("compile_blueprint", {"blueprint_name": "BP_SafeNode"}), "compile(BP_SafeNode)")

# ── Fix BP_AscensionGate ──
print("\n--- BP_AscensionGate: Fix exec connections ---")
r = mcp("analyze_blueprint_graph", {"blueprint_path": f"{BP}/BP_AscensionGate"})
if r and r.get("status") == "success":
    nodes = r["result"]["graph_data"]["nodes"]
    overlap = branch = print_n = None
    for n in nodes:
        t = n.get("title","")
        if "Overlap" in t: overlap = n["name"]
        elif "Branch" in t: branch = n["name"]
        elif "Print" in t: print_n = n["name"]

    if overlap and branch:
        conn("BP_AscensionGate", overlap, "then", branch, "execute")
    if branch and print_n:
        conn("BP_AscensionGate", branch, "then", print_n, "execute")

    ok(mcp("compile_blueprint", {"blueprint_name": "BP_AscensionGate"}), "compile(BP_AscensionGate)")

# ── Fix BP_SystemNoticePlaque ──
print("\n--- BP_SystemNoticePlaque: Fix exec connections ---")
r = mcp("analyze_blueprint_graph", {"blueprint_path": f"{BP}/BP_SystemNoticePlaque"})
if r and r.get("status") == "success":
    nodes = r["result"]["graph_data"]["nodes"]
    overlap = branch = print_n = varset = None
    for n in nodes:
        t = n.get("title","")
        if "Overlap" in t: overlap = n["name"]
        elif "Branch" in t: branch = n["name"]
        elif "Print" in t: print_n = n["name"]
        elif "Set" in t: varset = n["name"]

    if overlap and branch:
        conn("BP_SystemNoticePlaque", overlap, "then", branch, "execute")
    if branch and print_n:
        conn("BP_SystemNoticePlaque", branch, "else", print_n, "execute")  # else = NOT read
    if print_n and varset:
        conn("BP_SystemNoticePlaque", print_n, "then", varset, "execute")

    ok(mcp("compile_blueprint", {"blueprint_name": "BP_SystemNoticePlaque"}), "compile(BP_SystemNoticePlaque)")

print("\n=== Fix complete! ===")
