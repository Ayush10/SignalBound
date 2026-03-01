#!/usr/bin/env python3
"""Helper to send MCP commands to Unreal Editor plugin via TCP."""
import socket
import json
import sys

def send_command(cmd_type, params=None, timeout=30):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect(('127.0.0.1', 55557))

    command = {"type": cmd_type, "params": params or {}}
    sock.sendall(json.dumps(command).encode('utf-8'))

    chunks = []
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
        try:
            response = json.loads(b''.join(chunks).decode('utf-8'))
            sock.close()
            return response
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    sock.close()
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: mcp_cmd.py <command_type> [json_params]")
        sys.exit(1)

    cmd = sys.argv[1]
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    result = send_command(cmd, params)
    print(json.dumps(result, indent=2))
