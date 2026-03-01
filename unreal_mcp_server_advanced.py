#!/usr/bin/env python3
"""Local compatibility shim for Unreal MCP scripts.

This project-level shim mirrors the small subset of the external
`unreal_mcp_server_advanced.py` API used by local build scripts:
`get_unreal_connection().send_command(...)`.
"""

from __future__ import annotations

import json
import socket
import threading
from typing import Any, Dict, Optional


class UnrealConnection:
    """Tiny TCP client for the UnrealMCP editor bridge."""

    def __init__(self, host: str = "127.0.0.1", port: int = 55557) -> None:
        self.host = host
        self.port = port
        self._lock = threading.RLock()

    def send_command(
        self,
        command_type: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0,
    ) -> Dict[str, Any]:
        payload = {"type": command_type, "params": params or {}}
        encoded = json.dumps(payload).encode("utf-8")

        with self._lock:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                sock.connect((self.host, self.port))
                sock.sendall(encoded)

                chunks = []
                while True:
                    chunk = sock.recv(262144)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    try:
                        return json.loads(b"".join(chunks).decode("utf-8"))
                    except json.JSONDecodeError:
                        continue

                return {"status": "error", "error": "No response from Unreal"}
            except Exception as exc:
                return {"status": "error", "error": str(exc)}
            finally:
                sock.close()


_CONNECTION: Optional[UnrealConnection] = None


def get_unreal_connection() -> UnrealConnection:
    global _CONNECTION
    if _CONNECTION is None:
        _CONNECTION = UnrealConnection()
    return _CONNECTION

