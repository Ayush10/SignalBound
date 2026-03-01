#!/usr/bin/env python3
"""Add a readable baseline lighting rig to the current hub map via MCP.

This project uses a minimal MCP command set, so we cannot tweak per-light intensity
or post-process settings directly. To compensate, this script lays out a dense grid
of fill/flood lights so the hub stays readable during graybox iteration.
"""

from __future__ import annotations

import math
import sys
from typing import Any, Dict, List

from mcp_path import resolve_mcp_py_dir

MCP_PY_DIR = resolve_mcp_py_dir()
if str(MCP_PY_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_PY_DIR))

import unreal_mcp_server_advanced as server  # type: ignore

unreal = server.get_unreal_connection()


def send(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    resp = unreal.send_command(command, params)
    return resp or {"status": "error", "error": "No response"}


def is_ok(resp: Dict[str, Any]) -> bool:
    if resp.get("status") == "error":
        return False
    if resp.get("success") is False:
        return False
    return True


def delete_pattern(pattern: str) -> int:
    found = send("find_actors_by_name", {"pattern": pattern})
    if not is_ok(found):
        return 0
    removed = 0
    for actor in found.get("result", {}).get("actors", []):
        name = actor.get("name")
        if not name:
            continue
        send("delete_actor", {"name": name})
        removed += 1
    return removed


def spawn_light(
    actor_type: str,
    name: str,
    location: List[float],
    rotation: List[float] | None = None,
    scale: List[float] | None = None,
) -> bool:
    params: Dict[str, Any] = {
        "type": actor_type,
        "name": name,
        "location": location,
    }
    if rotation is not None:
        params["rotation"] = rotation
    if scale is not None:
        params["scale"] = scale
    return is_ok(send("spawn_actor", params))


def main() -> int:
    if not is_ok(send("ping", {})):
        print("ERROR: MCP ping failed")
        return 2

    # Reset only prior fix lights so script is repeatable.
    removed = 0
    removed += delete_pattern("L_FIX_")
    removed += delete_pattern("DirectionalLight_HubSun")
    removed += delete_pattern("DirectionalLight_HubFill")

    ok = 0
    fail = 0

    # Use a single directional light to avoid ForwardShadingPriority contention warnings.
    for spec in [
        ("DirectionalLight", "DirectionalLight_HubSun", [-6000, -5000, 9000], [-48, 36, 0]),
    ]:
        if spawn_light(spec[0], spec[1], spec[2], spec[3], [1, 1, 1]):
            ok += 1
        else:
            fail += 1

    # High ambient fill ring over hero district.
    radius = 15500
    for i in range(20):
        a = (2 * math.pi * i) / 20
        x = int(radius * math.cos(a))
        y = int(radius * math.sin(a))
        if spawn_light("PointLight", f"L_FIX_AmbientRing_{i:02d}", [x, y, 2600], None, [1, 1, 1]):
            ok += 1
        else:
            fail += 1

    # Dense flood grid to combat dark areas in a very large (300m+) hub footprint.
    # Spot lights are used because this MCP bridge cannot set point light attenuation.
    flood_x = [-17000, -11000, -5000, 1000, 7000, 13000, 19000]
    flood_y = [-16000, -10000, -4000, 2000, 8000, 14000]
    idx = 0
    for x in flood_x:
        for y in flood_y:
            if spawn_light(
                "SpotLight",
                f"L_FIX_Flood_{idx:03d}",
                [x, y, 3000],
                [90, 0, 0],
                [1, 1, 1],
            ):
                ok += 1
            else:
                fail += 1
            idx += 1

    # Path readability lights from hall -> dais -> armory -> gallery.
    path_lights = [
        (-13000, 0, 1500),
        (-9000, 0, 1500),
        (-5000, 0, 1500),
        (-1000, 0, 1500),
        (3500, -6500, 1300),
        (7500, -6100, 1300),
        (11600, 0, 1400),
        (13200, -3600, 1400),
        (13200, 0, 1400),
        (13200, 3600, 1400),
        (17000, 5200, 1700),
    ]
    for i, (x, y, z) in enumerate(path_lights):
        if spawn_light("SpotLight", f"L_FIX_Path_{i:02d}", [x, y, z], [90, 0, 0], [1, 1, 1]):
            ok += 1
        else:
            fail += 1

    # Subtle upward bounce lights in key plazas.
    bounce = [
        (-8000, 0, 100),
        (0, 0, 100),
        (4200, -7600, 100),
        (12800, 0, 100),
        (17000, 5200, 1300),
    ]
    for i, (x, y, z) in enumerate(bounce):
        if spawn_light("PointLight", f"L_FIX_Bounce_{i:02d}", [x, y, z], None, [1, 1, 1]):
            ok += 1
        else:
            fail += 1

    print(f"REMOVED={removed}")
    print(f"SPAWN_OK={ok}")
    print(f"SPAWN_FAIL={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
