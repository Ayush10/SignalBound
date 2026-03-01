#!/usr/bin/env python3
"""Create additive demo camera viewpoints across SignalBound maps.

This does not delete or rename existing world content.
It only adds missing CameraActor markers for quick manual demo navigation.
"""

from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MCPClient:
    host: str = "127.0.0.1"
    port: int = 55557
    throttle_s: float = 0.02

    def send(self, command_type: str, params: Optional[Dict[str, Any]] = None, timeout: float = 60.0) -> Dict[str, Any]:
        payload = {"type": command_type, "params": params or {}}
        data = json.dumps(payload).encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        time.sleep(self.throttle_s)
        try:
            sock.connect((self.host, self.port))
            sock.sendall(data)
            chunks: List[bytes] = []
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


def is_ok(resp: Dict[str, Any]) -> bool:
    return bool(resp) and resp.get("status") != "error" and resp.get("success") is not False


def actor_exists(c: MCPClient, name: str) -> bool:
    resp = c.send("find_actors_by_name", {"pattern": name})
    if not is_ok(resp):
        return False
    actors = (resp.get("result") or {}).get("actors") or []
    return any(a.get("name") == name for a in actors)


def ensure_camera(
    c: MCPClient,
    name: str,
    location: Tuple[float, float, float],
    rotation: Tuple[float, float, float],
    label: str,
) -> bool:
    if actor_exists(c, name):
        # Re-label existing camera to keep outliner names friendly and force dirty mark.
        c.send("set_actor_label", {"name": name, "label": label})
        return False

    resp = c.send(
        "spawn_actor",
        {
            "type": "CameraActor",
            "name": name,
            "location": [location[0], location[1], location[2]],
            "rotation": [rotation[0], rotation[1], rotation[2]],
            "scale": [1.0, 1.0, 1.0],
        },
    )
    if not is_ok(resp):
        raise RuntimeError(f"Failed spawning {name}: {resp.get('error', resp)}")

    # Label makes World Outliner tour navigation easier.
    c.send("set_actor_label", {"name": name, "label": label})
    return True


def load_map(c: MCPClient, map_path: str) -> None:
    resp = c.send("load_level", {"map_path": map_path}, timeout=120.0)
    if not is_ok(resp):
        raise RuntimeError(f"Failed to load {map_path}: {resp}")


def save_map(c: MCPClient) -> None:
    resp = c.send("save_current_level", {}, timeout=120.0)
    if not is_ok(resp):
        raise RuntimeError(f"Failed to save current level: {resp}")


def setup_map(c: MCPClient, map_path: str, cameras: List[Tuple[str, Tuple[float, float, float], Tuple[float, float, float], str]]) -> Tuple[int, int]:
    load_map(c, map_path)
    created = 0
    existing = 0
    for name, loc, rot, label in cameras:
        added = ensure_camera(c, name, loc, rot, label)
        if added:
            created += 1
        else:
            existing += 1
    save_map(c)
    return created, existing


def main() -> int:
    c = MCPClient()
    ping = c.send("ping", {}, timeout=5.0)
    if not is_ok(ping):
        print(f"ERROR: MCP not reachable: {ping}")
        return 2

    maps: Dict[str, List[Tuple[str, Tuple[float, float, float], Tuple[float, float, float], str]]] = {
        "/Game/Map_SystemTest": [
            ("DemoCam_SystemTest_Entry", (-2300, 0, 350), (0, 0, 0), "DemoCam: SystemTest Entry"),
            ("DemoCam_SystemTest_UIWall", (0, 2200, 350), (0, -90, 0), "DemoCam: SystemTest UI Wall"),
        ],
        "/Game/Map_HubCitadelCity": [
            ("DemoCam_Hub_GrandMirrorHall", (-18600, -7000, 420), (-5, 20, 0), "DemoCam: Hub Grand Mirror Hall"),
            ("DemoCam_Hub_SystemDais", (0, -3200, 1400), (-12, 0, 0), "DemoCam: Hub System Dais"),
            ("DemoCam_Hub_AscensionGallery", (0, 10400, 900), (-8, 0, 0), "DemoCam: Hub Ascension Gallery"),
            ("DemoCam_Hub_ContractTerrace", (0, -12000, 1100), (-10, 180, 0), "DemoCam: Hub Contract Terrace"),
            ("DemoCam_Hub_CloudVista", (0, -17000, 2200), (-18, 180, 0), "DemoCam: Hub Cloud Sea Vista"),
        ],
        "/Game/Map_Floor01_Ironcatacomb": [
            ("DemoCam_F1_EntrySafeNode", (-900, 0, 360), (-6, 0, 0), "DemoCam: F1 Entry Safe Node"),
            ("DemoCam_F1_Antechamber", (2200, -1300, 420), (-8, 22, 0), "DemoCam: F1 Room1 Antechamber"),
            ("DemoCam_F1_BranchSplit", (4200, 0, 450), (-8, 0, 0), "DemoCam: F1 Branch Split"),
            ("DemoCam_F1_SigilVault", (9600, -2100, 520), (-8, 24, 0), "DemoCam: F1 Sigil Vault"),
            ("DemoCam_F1_BossGateHall", (12100, 0, 520), (-6, 0, 0), "DemoCam: F1 Boss Gate Hall"),
            ("DemoCam_F1_BossArena", (15800, -2100, 900), (-10, 22, 0), "DemoCam: F1 Boss Arena"),
        ],
    }

    total_created = 0
    total_existing = 0

    for map_path, cams in maps.items():
        created, existing = setup_map(c, map_path, cams)
        total_created += created
        total_existing += existing
        print(f"MAP={map_path} CREATED={created} EXISTING={existing}")

    # End on hub map for immediate visual demo.
    load_map(c, "/Game/Map_HubCitadelCity")
    print(f"DEMO_CAMERAS_CREATED={total_created}")
    print(f"DEMO_CAMERAS_EXISTING={total_existing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
