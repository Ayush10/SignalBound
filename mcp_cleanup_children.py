#!/usr/bin/env python3
"""Clean up broken VariableSet nodes from child enemy BPs and apply CDO overrides
(requires plugin recompile for CDO support)."""
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

print("=== Cleaning up child enemy BPs ===\n")
r = mcp("ping")
if not r or r.get("status") != "success":
    print("MCP not reachable"); sys.exit(1)

# Child enemy overrides
CHILDREN = {
    "BP_Enemy_Thrall": {
        "MaxHealth": "60.0", "CurrentHealth": "60.0",
        "AttackDamage": "12.0", "ChaseSpeed": "300.0",
        "WindupDuration": "1.2", "RecoveryDuration": "1.5",
        "AttackRange": "180.0"
    },
    "BP_Enemy_Skitter": {
        "MaxHealth": "30.0", "CurrentHealth": "30.0",
        "AttackDamage": "8.0", "ChaseSpeed": "600.0",
        "WindupDuration": "0.4", "RecoveryDuration": "0.5",
        "AttackRange": "150.0", "StaggerThreshold": "15.0"
    },
    "BP_Enemy_Hexer": {
        "MaxHealth": "45.0", "CurrentHealth": "45.0",
        "AttackDamage": "18.0", "ChaseSpeed": "250.0",
        "WindupDuration": "1.0", "RecoveryDuration": "2.0",
        "AttackRange": "800.0", "DetectionRange": "1500.0",
        "bIsRanged": "true"
    },
    "BP_Elite_Oathguard": {
        "MaxHealth": "200.0", "CurrentHealth": "200.0",
        "AttackDamage": "35.0", "ChaseSpeed": "280.0",
        "WindupDuration": "1.5", "RecoveryDuration": "2.0",
        "AttackRange": "250.0", "StaggerThreshold": "60.0"
    },
}

for bp_name, overrides in CHILDREN.items():
    print(f"\n--- {bp_name} ---")

    # First, remove broken VariableSet nodes (they have no data pins)
    r = mcp("analyze_blueprint_graph", {"blueprint_path": f"/Game/Blueprints/{bp_name}"})
    if r and r.get("status") == "success":
        nodes = r["result"]["graph_data"]["nodes"]
        set_nodes = [n for n in nodes if "VariableSet" in n["name"]]
        if set_nodes:
            print(f"  Found {len(set_nodes)} broken VariableSet nodes, removing...")
            for n in set_nodes:
                r2 = mcp("remove_blueprint_node", {"blueprint_name": bp_name, "node_id": n["name"]})
                ok(r2, f"remove({n['name']})")

    # Try CDO approach (works only after plugin recompile)
    for var_name, val in overrides.items():
        r = mcp("set_blueprint_variable_properties", {
            "blueprint_name": bp_name,
            "variable_name": var_name,
            "default_value": val
        })
        result = r.get("result", {}) if r else {}
        if isinstance(result, dict) and result.get("success", False):
            ok(r, f"CDO({var_name}={val})")
        else:
            err = ""
            if isinstance(result, dict):
                err = result.get("error", "")
            elif r:
                err = r.get("error", "")
            if "Variable not found" in err:
                print(f"  SKIP: {var_name} (inherited var, CDO not available — needs plugin recompile)")
            else:
                print(f"  FAIL: {var_name} — {err[:80]}")

    ok(mcp("compile_blueprint", {"blueprint_name": bp_name}), f"compile({bp_name})")

# Add Oathguard extra vars
print("\n--- BP_Elite_Oathguard: Extra variables ---")
for var_name, vtype, default in [("bHasShield", "bool", "true"), ("ShieldHealth", "float", "100.0")]:
    r = mcp("create_variable", {
        "blueprint_name": "BP_Elite_Oathguard",
        "variable_name": var_name,
        "variable_type": vtype,
        "default_value": default,
        "category": "Config"
    })
    result = r.get("result", {}) if r else {}
    if isinstance(result, dict) and result.get("success", False):
        ok(r, f"var({var_name})")
    else:
        err = result.get("error","") if isinstance(result, dict) else r.get("error","") if r else ""
        if "Failed to create" in err:
            print(f"  SKIP: {var_name} (already exists)")
        else:
            print(f"  FAIL: {var_name} — {err[:80]}")

ok(mcp("compile_blueprint", {"blueprint_name": "BP_Elite_Oathguard"}), "compile(BP_Elite_Oathguard)")
print("\n=== Cleanup complete! ===")
print("\nNOTE: Child variable overrides require plugin recompile (Ctrl+Alt+F11 or restart editor)")
print("After recompile, re-run this script to apply CDO overrides.")
