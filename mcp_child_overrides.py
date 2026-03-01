#!/usr/bin/env python3
"""Set child enemy BP variable overrides using BeginPlay → Set nodes."""
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

def node(bp, ntype, params):
    r = mcp("add_blueprint_node", {"blueprint_name": bp, "node_type": ntype, "node_params": params})
    i = nid(r)
    ok(r, f"node({ntype})→{i[:20]}")
    return i

def conn(bp, src, spin, tgt, tpin):
    if not src or not tgt:
        print(f"  SKIP: missing id for conn({spin}→{tpin})")
        return False
    return ok(mcp("connect_nodes", {"blueprint_name": bp, "source_node_id": src, "source_pin_name": spin, "target_node_id": tgt, "target_pin_name": tpin}), f"conn({spin}→{tpin})")

def event(bp, ename):
    r = mcp("add_event_node", {"blueprint_name": bp, "event_name": ename})
    i = nid(r)
    ok(r, f"event({ename})→{i[:20]}")
    return i

def set_var_node(bp, var_name, value, value_type="float", pos_x=0, pos_y=0):
    """Add a VariableSet node for a parent variable."""
    r = mcp("add_blueprint_node", {
        "blueprint_name": bp,
        "node_type": "VariableSet",
        "node_params": {
            "variable_name": var_name,
            "pos_x": pos_x,
            "pos_y": pos_y
        }
    })
    i = nid(r)
    ok(r, f"VariableSet({var_name})→{i[:20]}")
    return i


# ── Child enemy overrides ──
# Each child needs BeginPlay → chain of Set nodes → Call Parent BeginPlay

CHILDREN = {
    "BP_Enemy_Thrall": {
        "MaxHealth": ("60.0", "float"),
        "AttackDamage": ("12.0", "float"),
        "ChaseSpeed": ("300.0", "float"),
        "WindupDuration": ("1.2", "float"),
        "RecoveryDuration": ("1.5", "float"),
        "AttackRange": ("180.0", "float"),
    },
    "BP_Enemy_Skitter": {
        "MaxHealth": ("30.0", "float"),
        "AttackDamage": ("8.0", "float"),
        "ChaseSpeed": ("600.0", "float"),
        "WindupDuration": ("0.4", "float"),
        "RecoveryDuration": ("0.5", "float"),
        "AttackRange": ("150.0", "float"),
        "StaggerThreshold": ("15.0", "float"),
    },
    "BP_Enemy_Hexer": {
        "MaxHealth": ("45.0", "float"),
        "AttackDamage": ("18.0", "float"),
        "ChaseSpeed": ("250.0", "float"),
        "WindupDuration": ("1.0", "float"),
        "RecoveryDuration": ("2.0", "float"),
        "AttackRange": ("800.0", "float"),
        "DetectionRange": ("1500.0", "float"),
        "bIsRanged": ("true", "bool"),
    },
    "BP_Elite_Oathguard": {
        "MaxHealth": ("200.0", "float"),
        "AttackDamage": ("35.0", "float"),
        "ChaseSpeed": ("280.0", "float"),
        "WindupDuration": ("1.5", "float"),
        "RecoveryDuration": ("2.0", "float"),
        "AttackRange": ("250.0", "float"),
        "StaggerThreshold": ("60.0", "float"),
    },
}

# Oathguard extra vars (new, not inherited)
OATHGUARD_EXTRA = {
    "bHasShield": ("bool", "true"),
    "ShieldHealth": ("float", "100.0"),
}

print("=== Setting child enemy variable overrides ===\n")
r = mcp("ping")
if not r or r.get("status") != "success":
    print("MCP not reachable"); sys.exit(1)

# First, try the CDO approach via set_blueprint_variable_properties
# This will work once the plugin is recompiled with our CDO fallback
# If it fails, we fall back to BeginPlay + Set nodes

for bp_name, overrides in CHILDREN.items():
    print(f"\n--- {bp_name} ---")

    # Try CDO approach first
    first_var = list(overrides.keys())[0]
    first_val = overrides[first_var][0]
    test = mcp("set_blueprint_variable_properties", {
        "blueprint_name": bp_name,
        "variable_name": first_var,
        "default_value": first_val
    })

    if test and test.get("status") == "success":
        result = test.get("result", {})
        if result.get("success", False):
            print(f"  CDO approach works! Setting all overrides...")
            # Set remaining vars via CDO
            for var_name, (val, vtype) in list(overrides.items())[1:]:
                r = mcp("set_blueprint_variable_properties", {
                    "blueprint_name": bp_name,
                    "variable_name": var_name,
                    "default_value": val
                })
                ok(r, f"CDO set {var_name}={val}")
            ok(mcp("compile_blueprint", {"blueprint_name": bp_name}), f"compile({bp_name})")
            continue

    # CDO didn't work — use BeginPlay + Set nodes
    print(f"  CDO unavailable, using BeginPlay + Set nodes...")

    # Check if BeginPlay already exists
    r = mcp("analyze_blueprint_graph", {"blueprint_path": f"/Game/Blueprints/{bp_name}"})
    bp_event_id = None
    if r and r.get("status") == "success":
        nodes = r["result"]["graph_data"]["nodes"]
        for n in nodes:
            if "BeginPlay" in n.get("title",""):
                bp_event_id = n["name"]

    if not bp_event_id:
        bp_event_id = event(bp_name, "ReceiveBeginPlay")

    print(f"  BeginPlay: {bp_event_id}")

    # Chain Set nodes: BeginPlay → Set1 → Set2 → ...
    prev_id = bp_event_id
    prev_pin = "then"

    y_offset = 0
    for var_name, (val, vtype) in overrides.items():
        # Create a Set node for this variable
        set_id = set_var_node(bp_name, var_name, val, vtype, pos_x=300 + y_offset * 50, pos_y=y_offset * 100)

        if set_id:
            # Connect exec chain
            conn(bp_name, prev_id, prev_pin, set_id, "execute")

            # Set the value on the set node's input pin
            # The pin name for the value input on a Set node is the variable name
            # We need to create a literal node for the value
            if vtype == "float":
                literal_id = node(bp_name, "LiteralFloat", {
                    "value": float(val),
                    "pos_x": 200 + y_offset * 50,
                    "pos_y": y_offset * 100 + 50
                })
                if literal_id and set_id:
                    conn(bp_name, literal_id, "ReturnValue", set_id, var_name)
            elif vtype == "bool":
                literal_id = node(bp_name, "LiteralBool", {
                    "value": val == "true",
                    "pos_x": 200 + y_offset * 50,
                    "pos_y": y_offset * 100 + 50
                })
                if literal_id and set_id:
                    conn(bp_name, literal_id, "ReturnValue", set_id, var_name)

            prev_id = set_id
            prev_pin = "then"
        y_offset += 1

    ok(mcp("compile_blueprint", {"blueprint_name": bp_name}), f"compile({bp_name})")

# Add extra vars to Oathguard
print("\n--- BP_Elite_Oathguard: Extra variables ---")
for var_name, (vtype, default) in OATHGUARD_EXTRA.items():
    r = mcp("create_variable", {
        "blueprint_name": "BP_Elite_Oathguard",
        "variable_name": var_name,
        "variable_type": vtype,
        "default_value": default,
        "category": "Config"
    })
    ok(r, f"var({var_name})")

ok(mcp("compile_blueprint", {"blueprint_name": "BP_Elite_Oathguard"}), "compile(BP_Elite_Oathguard)")

print("\n=== Child overrides complete! ===")
