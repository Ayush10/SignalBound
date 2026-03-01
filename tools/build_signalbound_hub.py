#!/usr/bin/env python3
"""Build SignalBound hub geometry in the currently open Unreal level via MCP."""

from __future__ import annotations

import math
import argparse
import sys
from typing import Any, Dict, List, Tuple

from mcp_path import resolve_mcp_py_dir

MCP_PY_DIR = resolve_mcp_py_dir()
if str(MCP_PY_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_PY_DIR))

import unreal_mcp_server_advanced as server  # type: ignore


CUBE = "/Engine/BasicShapes/Cube.Cube"
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"
SPHERE = "/Engine/BasicShapes/Sphere.Sphere"
PLANE = "/Engine/BasicShapes/Plane.Plane"
CONE = "/Engine/BasicShapes/Cone.Cone"

unreal = server.get_unreal_connection()

spawned: List[str] = []
failed: List[Tuple[str, str]] = []
skipped_existing = 0
overwrite_existing = False


def send(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    resp = unreal.send_command(command, params)
    if not resp:
        return {"status": "error", "error": "No response"}
    return resp


def is_ok(resp: Dict[str, Any]) -> bool:
    if resp.get("status") == "error":
        return False
    if resp.get("success") is False:
        return False
    return True


def delete_if_exists(name: str) -> None:
    send("delete_actor", {"name": name})


def spawn_mesh(
    name: str,
    location: List[float],
    scale: List[float],
    rotation: List[float] | None = None,
    mesh: str = CUBE,
) -> None:
    global skipped_existing
    if overwrite_existing:
        delete_if_exists(name)
    params: Dict[str, Any] = {
        "type": "StaticMeshActor",
        "name": name,
        "location": location,
        "scale": scale,
        "static_mesh": mesh,
    }
    if rotation is not None:
        params["rotation"] = rotation
    resp = send("spawn_actor", params)
    if is_ok(resp):
        spawned.append(name)
    else:
        err = resp.get("error", str(resp))
        if (not overwrite_existing) and ("already exists" in str(err).lower()):
            skipped_existing += 1
            return
        failed.append((name, err))


def spawn_light(
    name: str,
    actor_type: str,
    location: List[float],
    rotation: List[float] | None = None,
    scale: List[float] | None = None,
) -> None:
    global skipped_existing
    if overwrite_existing:
        delete_if_exists(name)
    params: Dict[str, Any] = {
        "type": actor_type,
        "name": name,
        "location": location,
    }
    if rotation is not None:
        params["rotation"] = rotation
    if scale is not None:
        params["scale"] = scale
    resp = send("spawn_actor", params)
    if is_ok(resp):
        spawned.append(name)
    else:
        err = resp.get("error", str(resp))
        if (not overwrite_existing) and ("already exists" in str(err).lower()):
            skipped_existing += 1
            return
        failed.append((name, err))


def clear_level_geometry() -> None:
    resp = send("get_actors_in_level", {})
    if not is_ok(resp):
        raise RuntimeError(f"Failed to get actor list: {resp}")

    actors = resp.get("result", {}).get("actors", [])
    keep_classes = {
        "WorldSettings",
        "Brush",
        "WorldDataLayers",
        "DefaultPhysicsVolume",
        "GameplayDebuggerPlayerManager",
        "AbstractNavData",
    }
    keep_prefixes = (
        "WorldPartitionMiniMap",
        "ChaosDebugDrawActor",
    )

    for actor in actors:
        name = actor.get("name", "")
        cls = actor.get("class", "")
        if cls in keep_classes:
            continue
        if any(name.startswith(p) for p in keep_prefixes):
            continue
        send("delete_actor", {"name": name})


def build_grand_mirror_hall() -> None:
    # Core hall floor and side channels
    spawn_mesh("SM_GMH_Floor_Main", [-8000, 0, -120], [160, 60, 0.4], mesh=CUBE)
    spawn_mesh("SM_GMH_Channel_Left", [-8000, -2500, -100], [160, 6, 0.1], mesh=CUBE)
    spawn_mesh("SM_GMH_Channel_Right", [-8000, 2500, -100], [160, 6, 0.1], mesh=CUBE)

    # Repeating arches
    x0 = -14000
    for i in range(7):
        x = x0 + i * 2000
        spawn_mesh(f"SM_GMH_Arch_{i:02d}_L", [x, -2100, 450], [1.2, 1.2, 9], mesh=CUBE)
        spawn_mesh(f"SM_GMH_Arch_{i:02d}_R", [x, 2100, 450], [1.2, 1.2, 9], mesh=CUBE)
        spawn_mesh(f"SM_GMH_Arch_{i:02d}_Top", [x, 0, 900], [1.4, 44, 1], mesh=CUBE)
        spawn_mesh(f"SM_GMH_Glass_{i:02d}", [x, -1800, 700], [0.1, 6, 5], mesh=PLANE)
        spawn_mesh(f"SM_GMH_Glass_{i:02d}_B", [x, 1800, 700], [0.1, 6, 5], mesh=PLANE)

    # Floating shard canopy
    for i in range(18):
        x = -12000 + i * 700
        y = -1200 + ((i % 6) * 480)
        z = 1700 + (i % 3) * 140
        yaw = (i * 37) % 360
        spawn_mesh(f"SM_GMH_Shards_{i:02d}", [x, y, z], [0.15, 1.1, 0.08], [12, yaw, 32], mesh=CUBE)

    # Entry lighting
    for i in range(6):
        x = -13000 + i * 2200
        spawn_light(f"L_GMH_WarmSpot_{i:02d}", "SpotLight", [x, 0, 1400], [90, 0, 0], [1, 1, 1])


def build_system_dais() -> None:
    spawn_mesh("SM_SD_Pool_Base", [0, 0, -160], [70, 70, 0.2], mesh=CYL)
    spawn_mesh("SM_SD_Dais_Main", [0, 0, 20], [34, 34, 0.5], mesh=CYL)
    spawn_mesh("SM_SD_Dais_Ring", [0, 0, 120], [42, 42, 0.15], mesh=CYL)
    spawn_mesh("SM_SD_Crystal_Core", [0, 0, 900], [4.5, 4.5, 11], mesh=CONE)

    # Floating ring made from shard segments
    ring_r = 950
    for i in range(16):
        a = (2 * math.pi * i) / 16
        x = ring_r * math.cos(a)
        y = ring_r * math.sin(a)
        yaw = math.degrees(a) + 90
        spawn_mesh(f"SM_SD_RingSeg_{i:02d}", [x, y, 900], [0.2, 2.2, 0.25], [0, yaw, 0], mesh=CUBE)

    spawn_light("L_SD_MoonKey", "DirectionalLight", [-2000, -1400, 2200], [-55, 35, 0], [1, 1, 1])
    for i in range(8):
        a = (2 * math.pi * i) / 8
        x = 2500 * math.cos(a)
        y = 2500 * math.sin(a)
        spawn_light(f"L_SD_Rim_{i:02d}", "PointLight", [x, y, 450], None, [1, 1, 1])


def build_armory_archive() -> None:
    # Armory deck
    spawn_mesh("SM_AA_Armory_Floor", [3800, -7600, -110], [58, 32, 0.4], mesh=CUBE)
    for i in range(8):
        x = 2100 + i * 700
        spawn_mesh(f"SM_AA_WeaponRack_{i:02d}", [x, -8450, 180], [0.2, 5, 2.4], mesh=CUBE)
    for i in range(5):
        x = 2600 + i * 1000
        spawn_mesh(f"SM_AA_RelicPedestal_{i:02d}", [x, -7000, 120], [1.2, 1.2, 2.0], mesh=CYL)
        spawn_mesh(f"SM_AA_BladeRelic_{i:02d}", [x, -7000, 360], [0.12, 1.3, 0.12], [0, i * 24, 30], mesh=CUBE)

    # Archive steps
    for i in range(7):
        spawn_mesh(
            f"SM_AA_ArchiveStep_{i:02d}",
            [7600 + i * 420, -6200, -80 + i * 65],
            [4.5, 20, 0.35],
            mesh=CUBE,
        )
    for i in range(10):
        x = 7900 + (i % 5) * 500
        z = 420 + (i // 5) * 160
        spawn_mesh(f"SM_AA_ScrollTube_{i:02d}", [x, -5450, z], [0.6, 0.6, 2.1], [90, 0, 0], mesh=CYL)
    for i in range(6):
        x = 7900 + i * 520
        spawn_mesh(f"SM_AA_BookStack_{i:02d}", [x, -5050, 220], [1.4, 1.0, 1.2], mesh=CUBE)

    for i in range(6):
        spawn_light(f"L_AA_Warm_{i:02d}", "PointLight", [2500 + i * 1000, -7600, 500], None, [1, 1, 1])


def build_ascension_gallery() -> None:
    spawn_mesh("SM_AG_Floor", [12800, 0, -100], [42, 90, 0.4], mesh=CUBE)
    door_y = [-3600, 0, 3600]

    for idx, y in enumerate(door_y):
        # Cathedral frame
        spawn_mesh(f"SM_AG_Door_{idx:02d}_PillarL", [13650, y - 950, 650], [1.4, 1.4, 12], mesh=CUBE)
        spawn_mesh(f"SM_AG_Door_{idx:02d}_PillarR", [13650, y + 950, 650], [1.4, 1.4, 12], mesh=CUBE)
        spawn_mesh(f"SM_AG_Door_{idx:02d}_Top", [13650, y, 1250], [1.6, 20, 1.2], mesh=CUBE)
        spawn_mesh(f"SM_AG_Door_{idx:02d}_Seal", [13720, y, 700], [7.2, 7.2, 0.12], [90, 0, 0], mesh=CYL)

        # Door pads
        spawn_mesh(f"SM_AG_DoorPad_{idx:02d}", [12600, y, -60], [4.2, 4.2, 0.2], mesh=CYL)

        # Faceless guardians + lowered blades
        spawn_mesh(f"SM_AG_Guardian_{idx:02d}_L", [13100, y - 1700, 520], [1.5, 1.5, 8.5], mesh=CUBE)
        spawn_mesh(f"SM_AG_Guardian_{idx:02d}_R", [13100, y + 1700, 520], [1.5, 1.5, 8.5], mesh=CUBE)
        spawn_mesh(f"SM_AG_Blade_{idx:02d}_L", [13100, y - 1700, 120], [0.2, 0.7, 3.4], mesh=CUBE)
        spawn_mesh(f"SM_AG_Blade_{idx:02d}_R", [13100, y + 1700, 120], [0.2, 0.7, 3.4], mesh=CUBE)

    # Cracked first door look
    for i in range(8):
        spawn_mesh(
            f"SM_AG_Door00_Crack_{i:02d}",
            [13780, -3600 + i * 90, 520 + i * 55],
            [0.05, 0.6, 1.1],
            [0, i * 13, -20 + i * 5],
            mesh=CUBE,
        )


def build_city_exterior_ring() -> None:
    # Ring roads / plazas
    spawn_mesh("SM_EXT_Road_N", [0, 13800, -140], [190, 14, 0.25], mesh=CUBE)
    spawn_mesh("SM_EXT_Road_S", [0, -13800, -140], [190, 14, 0.25], mesh=CUBE)
    spawn_mesh("SM_EXT_Road_E", [13800, 0, -140], [14, 190, 0.25], mesh=CUBE)
    spawn_mesh("SM_EXT_Road_W", [-13800, 0, -140], [14, 190, 0.25], mesh=CUBE)

    # Canal lines
    spawn_mesh("SM_EXT_Canal_N", [0, 12200, -120], [190, 4, 0.08], mesh=CUBE)
    spawn_mesh("SM_EXT_Canal_S", [0, -12200, -120], [190, 4, 0.08], mesh=CUBE)
    spawn_mesh("SM_EXT_Canal_E", [12200, 0, -120], [4, 190, 0.08], mesh=CUBE)
    spawn_mesh("SM_EXT_Canal_W", [-12200, 0, -120], [4, 190, 0.08], mesh=CUBE)

    # Skyline silhouettes
    for i in range(16):
        x = -22000 + i * 2800
        h = 6 + (i % 5) * 4
        spawn_mesh(f"SM_EXT_Skyline_N_{i:02d}", [x, 22000, h * 60], [9, 9, h], mesh=CUBE)
        spawn_mesh(f"SM_EXT_Skyline_S_{i:02d}", [x, -22000, h * 60], [9, 9, h], mesh=CUBE)
    for i in range(12):
        y = -16000 + i * 3000
        h = 8 + (i % 4) * 5
        spawn_mesh(f"SM_EXT_Skyline_E_{i:02d}", [22000, y, h * 60], [8, 8, h], mesh=CUBE)
        spawn_mesh(f"SM_EXT_Skyline_W_{i:02d}", [-22000, y, h * 60], [8, 8, h], mesh=CUBE)

    # Lampposts / banners / benches / planters
    idx = 0
    for x in range(-12000, 12001, 3000):
        for y in (-12000, 12000):
            spawn_mesh(f"SM_EXT_Lamp_{idx:02d}", [x, y, 340], [0.35, 0.35, 7], mesh=CYL)
            spawn_mesh(f"SM_EXT_Banner_{idx:02d}", [x + 220, y, 650], [0.08, 2.2, 2.5], mesh=PLANE)
            spawn_light(f"L_EXT_Lamp_{idx:02d}", "PointLight", [x, y, 760], None, [1, 1, 1])
            idx += 1

    for i in range(10):
        x = -9000 + i * 1800
        spawn_mesh(f"SM_EXT_Bench_N_{i:02d}", [x, 10400, 20], [2.4, 0.7, 0.6], mesh=CUBE)
        spawn_mesh(f"SM_EXT_Bench_S_{i:02d}", [x, -10400, 20], [2.4, 0.7, 0.6], mesh=CUBE)
        spawn_mesh(f"SM_EXT_Planter_N_{i:02d}", [x, 9600, 50], [1.5, 1.5, 1], mesh=CYL)
        spawn_mesh(f"SM_EXT_Planter_S_{i:02d}", [x, -9600, 50], [1.5, 1.5, 1], mesh=CYL)

    # Elevated terrace vista
    spawn_mesh("SM_VISTA_TerraceDeck", [17000, 5200, 1300], [28, 16, 0.3], mesh=CUBE)
    spawn_mesh("SM_VISTA_TerraceBridge", [14500, 5200, 900], [24, 8, 0.2], mesh=CUBE)
    spawn_mesh("SM_VISTA_BalconyBroken", [18200, 5200, 1450], [10, 0.5, 2], mesh=CUBE)
    for i in range(12):
        spawn_mesh(
            f"SM_VISTA_BrokenEdge_{i:02d}",
            [18200 + i * 40, 4800 + i * 60, 1530 + ((i % 3) * 30)],
            [0.12, 0.45, 0.2],
            [0, i * 17, 0],
            mesh=CUBE,
        )

    # Distant vertical tower descending beneath cloudline
    spawn_mesh("SM_VISTA_DarkTower", [25000, 5200, -18000], [18, 18, 380], mesh=CYL)
    for i in range(30):
        z = -2200 - i * 1200
        spawn_mesh(f"SM_VISTA_VoidDust_{i:02d}", [23600 + (i % 6) * 320, 4300 + (i % 5) * 210, z], [0.12, 0.12, 0.12], mesh=SPHERE)


def place_markers_and_props() -> None:
    # Required markers
    spawn_mesh("BP_PlayerStart_Map_HubCitadelCity", [-14600, 0, 120], [0.6, 0.6, 2.0], mesh=CYL)
    spawn_mesh("BP_SafeNode_00", [-13650, 600, 120], [0.55, 0.55, 1.3], mesh=SPHERE)
    spawn_mesh("BP_AscensionGate_00", [12600, -3600, 20], [0.8, 0.8, 2.0], mesh=CYL)
    spawn_mesh("BP_AscensionGate_01", [12600, 0, 20], [0.8, 0.8, 2.0], mesh=CYL)
    spawn_mesh("BP_AscensionGate_02", [12600, 3600, 20], [0.8, 0.8, 2.0], mesh=CYL)

    # Ambient system notice plaques
    plaque_positions = [
        (-11800, -1800, 120),
        (-4200, 1800, 120),
        (3500, -6500, 120),
        (9800, 2500, 120),
        (16000, 5400, 1420),
    ]
    for i, (x, y, z) in enumerate(plaque_positions):
        spawn_mesh(f"BP_SystemNoticePlaque_{i:02d}", [x, y, z], [0.3, 2.0, 1.3], mesh=CUBE)

    # Spawn-group anchor markers (tag proxy due MCP tag limitation)
    group_names = [
        "SpawnGroup_HubAmbient",
        "SpawnGroup_Floor01_Room1",
        "SpawnGroup_Floor01_Room2",
        "SpawnGroup_Floor01_Room3",
        "SpawnGroup_Floor02_Room1",
        "SpawnGroup_Floor02_Room2",
        "SpawnGroup_Floor02_Room3",
        "SpawnGroup_Floor03_Room1",
        "SpawnGroup_Floor03_Room2",
        "SpawnGroup_Floor03_Room3",
    ]
    for idx, group in enumerate(group_names):
        x = -15000 + idx * 800
        spawn_mesh(f"TagMarker_{group}", [x, 9800, 60], [0.25, 0.25, 0.25], mesh=SPHERE)


def build_systemtest_room() -> None:
    # Simple enclosed square room + one test player marker.
    spawn_mesh("ST_Floor", [0, 0, -100], [30, 30, 0.4], mesh=CUBE)
    spawn_mesh("ST_Ceiling", [0, 0, 900], [30, 30, 0.2], mesh=CUBE)
    spawn_mesh("ST_Wall_N", [0, 3000, 400], [30, 0.4, 10], mesh=CUBE)
    spawn_mesh("ST_Wall_S", [0, -3000, 400], [30, 0.4, 10], mesh=CUBE)
    spawn_mesh("ST_Wall_E", [3000, 0, 400], [0.4, 30, 10], mesh=CUBE)
    spawn_mesh("ST_Wall_W", [-3000, 0, 400], [0.4, 30, 10], mesh=CUBE)
    spawn_light("ST_KeyLight", "PointLight", [0, 0, 700], None, [1, 1, 1])
    spawn_mesh("BP_PlayerStart_Map_SystemTest", [0, 0, 120], [0.6, 0.6, 2.0], mesh=CYL)
    spawn_mesh("ST_UI_Wall_Empty", [0, 2980, 350], [12, 0.12, 6], mesh=CUBE)


def main() -> int:
    global overwrite_existing
    parser = argparse.ArgumentParser(description="Build SignalBound hub in current level.")
    parser.add_argument(
        "--phase",
        choices=[
            "all",
            "clear",
            "grand_hall",
            "system_dais",
            "armory_archive",
            "ascension_gallery",
            "city_exterior",
            "markers",
            "systemtest_room",
        ],
        default="all",
    )
    parser.add_argument(
        "--allow-clear",
        action="store_true",
        help="Required to run destructive clear operations.",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Replace actors with matching names instead of preserving them.",
    )
    args = parser.parse_args()
    overwrite_existing = args.overwrite_existing

    ping = send("ping", {})
    if not is_ok(ping):
        print(f"ERROR: Unreal MCP ping failed: {ping}")
        return 2

    phase = args.phase
    if phase == "clear" and not args.allow_clear:
        print("ERROR: --phase clear requires --allow-clear to avoid accidental data loss.")
        return 3
    if (phase == "clear") or (phase == "all" and args.allow_clear):
        clear_level_geometry()
        print("PHASE_DONE=clear_level_geometry", flush=True)
    if phase in ("all", "grand_hall"):
        build_grand_mirror_hall()
        print("PHASE_DONE=build_grand_mirror_hall", flush=True)
    if phase in ("all", "system_dais"):
        build_system_dais()
        print("PHASE_DONE=build_system_dais", flush=True)
    if phase in ("all", "armory_archive"):
        build_armory_archive()
        print("PHASE_DONE=build_armory_archive", flush=True)
    if phase in ("all", "ascension_gallery"):
        build_ascension_gallery()
        print("PHASE_DONE=build_ascension_gallery", flush=True)
    if phase in ("all", "city_exterior"):
        build_city_exterior_ring()
        print("PHASE_DONE=build_city_exterior_ring", flush=True)
    if phase in ("all", "markers"):
        place_markers_and_props()
        print("PHASE_DONE=place_markers_and_props", flush=True)
    if phase in ("all", "systemtest_room"):
        build_systemtest_room()
        print("PHASE_DONE=build_systemtest_room", flush=True)

    print(f"SPAWNED_COUNT={len(spawned)}")
    print(f"SKIPPED_EXISTING_COUNT={skipped_existing}")
    if failed:
        print(f"FAILED_COUNT={len(failed)}")
        for name, err in failed[:25]:
            print(f"FAILED {name}: {err}")
    else:
        print("FAILED_COUNT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
