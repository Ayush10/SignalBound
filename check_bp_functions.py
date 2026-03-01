import json, socket

def send(cmd_type, params):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(20)
        sock.connect(("127.0.0.1", 55557))
        payload = json.dumps({"type": cmd_type, "params": params}).encode("utf-8")
        sock.sendall(payload)
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                return json.loads(b"".join(chunks).decode("utf-8"))
            except Exception:
                continue
    return {"status": "error", "error": "no response"}

bps = [
    "BP_PlayerCharacter",
    "BP_EnemyBase",
    "BP_ContractManager",
    "BP_SystemManager",
    "BP_HUDManager",
    "BP_SignalBoundGameMode",
]

for bp in bps:
    r = send("read_blueprint_content", {"blueprint_path": f"/Game/Blueprints/{bp}"})
    print(f"\n=== {bp} ===")
    if r.get("status") != "success":
        print(r)
        continue
    funcs = r.get("result", {}).get("functions", [])
    for f in funcs:
        if f.get("graph_type") == "Function":
            print(f"  function: {f.get('name')} | nodes:{f.get('node_count', 0)} | parent_call?:{f.get('overrides_parent', False)}")
