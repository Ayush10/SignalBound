#!/usr/bin/env python3
import json
import socket

HOST = "127.0.0.1"
PORT = 55557


def send(cmd_type, params):
    payload = json.dumps({"type": cmd_type, "params": params}).encode("utf-8")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
        s.sendall(payload)
        buf = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            try:
                return json.loads(buf.decode("utf-8"))
            except json.JSONDecodeError:
                continue
        return {"status":"error","error":"No response"}
    except Exception as exc:
        return {"status":"error","error": str(exc)}
    finally:
        s.close()


def read_bp(path):
    return send("read_blueprint_content", {"blueprint_path": path})


def delete_bp_function(bp_name, func):
    return send("delete_function", {"blueprint_name": bp_name, "function_name": func})

bPs = [
    "BP_PlayerCharacter",
    "BP_EnemyBase",
    "BP_ContractManager",
    "BP_SystemManager",
    "BP_HUDManager",
]

for bp in bPs:
    print(f"--- {bp}")
    res = read_bp(f"/Game/Blueprints/{bp}")
    if res.get("status") != "success":
        print(f"read failed: {res}")
        continue

    functions = res["result"].get("functions", [])
    to_delete = [f["name"] for f in functions if f.get("graph_type") == "Function" and f.get("name") != "UserConstructionScript"]

    if not to_delete:
        print(" no delete candidates")
        continue

    for fn in to_delete:
        out = delete_bp_function(bp, fn)
        if out.get("status") == "success":
            print(f" deleted {fn}")
        else:
            print(f" failed {fn}: {out}")

print('--- compile sweep')
for bp in bPs + ["BP_SignalBoundGameMode"]:
    out = send("compile_blueprint", {"blueprint_name": bp})
    print(f"compile {bp}: {out.get('status')} {out}")
