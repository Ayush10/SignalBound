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
                return json.loads(b"".join(chunks).decode('utf-8'))
            except Exception:
                continue
    return {"status":"error","error":"no response"}

r = send("analyze_blueprint_graph", {"blueprint_path":"/Game/Blueprints/BP_PlayerCharacter"})
print(r)
