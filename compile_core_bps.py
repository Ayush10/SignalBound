import json, socket


def send(cmd_type, params):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(20)
        sock.connect(("127.0.0.1", 55557))
        sock.sendall(json.dumps({"type": cmd_type, "params": params}).encode("utf-8"))
        chunks = []
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                return json.loads(b"".join(chunks).decode('utf-8'))
            except Exception:
                continue
    return {"status":"error","error":"no response"}

bps = [
    '/Game/Blueprints/BP_PlayerCharacter',
    '/Game/Blueprints/BP_EnemyBase',
    '/Game/Blueprints/BP_ContractManager',
    '/Game/Blueprints/BP_SystemManager',
    '/Game/Blueprints/BP_HUDManager',
    '/Game/Blueprints/BP_SignalBoundGameMode',
]

for bp in bps:
    r = send('compile_blueprint', {'blueprint_name': bp})
    print(f"{bp}: {r}")
