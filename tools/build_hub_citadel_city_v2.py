#!/usr/bin/env python3
"""Build Map_HubCitadelCity as a vibrant Signal metropolis (phased)."""

from __future__ import annotations

import argparse
import math
import random
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

MATS = {
    "marble": "/Game/LevelPrototyping/Materials/MI_DefaultColorway.MI_DefaultColorway",
    "stone": "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray_02.MI_PrototypeGrid_Gray_02",
    "iron": "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark.MI_PrototypeGrid_TopDark",
    "gold": "/Game/ThirdPerson/MI_ThirdPersonColWay.MI_ThirdPersonColWay",
    "bronze": "/Game/Characters/Mannequins/Materials/Manny/MI_Manny_01_New.MI_Manny_01_New",
    "cyan": "/Game/Characters/Mannequins/Materials/Quinn/MI_Quinn_01.MI_Quinn_01",
    "teal": "/Game/Characters/Mannequins/Materials/Manny/MI_Manny_02_New.MI_Manny_02_New",
    "violet": "/Game/Characters/Mannequins/Materials/Quinn/MI_Quinn_02.MI_Quinn_02",
    "crimson": "/Game/Variant_Combat/Materials/M_Lava.M_Lava",
}

unreal = server.get_unreal_connection()

spawned: List[str] = []
failed: List[Tuple[str, str]] = []
materials_applied = 0
skipped_existing = 0
overwrite_existing = False


def send(command: str, params: Dict[str, Any]) -> Dict[str, Any]:
    resp = unreal.send_command(command, params)
    return resp or {"status": "error", "error": "No response"}


def is_ok(resp: Dict[str, Any]) -> bool:
    if resp.get("status") == "error":
        return False
    if resp.get("success") is False:
        return False
    return True


def delete_if_exists(name: str) -> None:
    send("delete_actor", {"name": name})


def delete_by_pattern(pattern: str) -> int:
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


def spawn_mesh(
    name: str,
    location: List[float],
    scale: List[float],
    rotation: List[float] | None = None,
    mesh: str = CUBE,
) -> bool:
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
        return True
    err = resp.get("error", str(resp))
    if (not overwrite_existing) and ("already exists" in str(err).lower()):
        skipped_existing += 1
        return False
    failed.append((name, err))
    return False


def spawn_light(
    name: str,
    actor_type: str,
    location: List[float],
    rotation: List[float] | None = None,
    scale: List[float] | None = None,
) -> bool:
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
        return True
    err = resp.get("error", str(resp))
    if (not overwrite_existing) and ("already exists" in str(err).lower()):
        skipped_existing += 1
        return False
    failed.append((name, err))
    return False


def apply_mat(actor_name: str, mat_path: str) -> bool:
    global materials_applied
    resp = send(
        "apply_material_to_actor",
        {"actor_name": actor_name, "material_path": mat_path, "material_slot": 0},
    )
    if is_ok(resp):
        materials_applied += 1
        return True
    failed.append((f"mat:{actor_name}", resp.get("error", str(resp))))
    return False


def spawn_colored_mesh(
    name: str,
    location: List[float],
    scale: List[float],
    mat: str,
    rotation: List[float] | None = None,
    mesh: str = CUBE,
) -> None:
    if spawn_mesh(name, location, scale, rotation, mesh):
        apply_mat(name, mat)


def clear_existing_hub() -> int:
    patterns = [
        "SM_GMH_",
        "SM_SD_",
        "SM_AA_",
        "SM_AG_",
        "SM_EXT_",
        "SM_VISTA_",
        "SM_GARDEN_",
        "SM_FLOWER_",
        "SM_Rose_",
        "L_FIX_",
        "L_BEAUTY_",
        "L_GMH_",
        "L_SD_",
        "L_AA_",
        "L_AG_",
        "SM_CORE_",
        "SM_SIG_",
        "SM_CON_",
        "SM_RES_",
        "SM_SKY_",
        "SM_TRN_",
        "SM_ARENA_",
        "SM_OUT_",
        "SM_UND_",
        "SM_CLOUD_",
        "SM_VEH_",
        "L_CORE_",
        "L_SIG_",
        "L_CON_",
        "L_SKY_",
        "L_OUT_",
        "BP_PlayerStart_Map_HubCitadelCity",
        "BP_SafeNode_00",
        "BP_AscensionGate_00",
        "BP_AscensionGate_01",
        "BP_AscensionGate_02",
        "BP_SystemNoticePlaque_",
        "TagMarker_SpawnGroup_",
    ]
    removed = 0
    for p in patterns:
        removed += delete_by_pattern(p)
    return removed


def build_sovereign_core() -> None:
    # Core city plate and boulevard loop (400m class playable footprint).
    spawn_colored_mesh("SM_CORE_CityPlate", [0, 0, -220], [260, 260, 0.2], MATS["stone"])
    spawn_colored_mesh("SM_CORE_Boulevard_NS", [0, 0, -120], [18, 210, 0.22], MATS["marble"])
    spawn_colored_mesh("SM_CORE_Boulevard_EW", [0, 0, -120], [210, 18, 0.22], MATS["marble"])

    ring_r = 14000
    for i in range(24):
        a = (2.0 * math.pi * i) / 24.0
        x = ring_r * math.cos(a)
        y = ring_r * math.sin(a)
        yaw = math.degrees(a) + 90
        spawn_colored_mesh(
            f"SM_CORE_Loop_{i:02d}",
            [x, y, -115],
            [2.1, 24, 0.2],
            MATS["marble"],
            [0, yaw, 0],
        )
        if i % 2 == 0:
            spawn_colored_mesh(
                f"SM_CORE_CyanConduit_{i:02d}",
                [x, y, -95],
                [0.15, 20, 0.06],
                MATS["cyan"],
                [0, yaw, 0],
            )

    # District connectors.
    spawn_colored_mesh("SM_CORE_Path_Armory", [6500, 0, -112], [60, 6, 0.18], MATS["marble"])
    spawn_colored_mesh("SM_CORE_Path_Archive", [-6500, 0, -112], [60, 6, 0.18], MATS["marble"])
    spawn_colored_mesh("SM_CORE_Path_Ascension", [0, 7000, -112], [6, 60, 0.18], MATS["marble"])
    spawn_colored_mesh("SM_CORE_Path_Contract", [0, -7000, -112], [6, 60, 0.18], MATS["marble"])
    spawn_colored_mesh("SM_CORE_Path_EntryA", [-9000, -4500, -112], [52, 6, 0.18], MATS["marble"])
    spawn_colored_mesh("SM_CORE_Path_EntryB", [-12000, -2500, -112], [6, 40, 0.18], MATS["marble"])

    # 4.1 Grand Mirror Hall (SW entry).
    spawn_colored_mesh("SM_CORE_GMH_Floor", [-16000, -7000, -110], [40, 15, 0.2], MATS["marble"])
    spawn_colored_mesh("SM_CORE_GMH_Channel_L", [-16000, -8200, -98], [40, 1.8, 0.06], MATS["cyan"])
    spawn_colored_mesh("SM_CORE_GMH_Channel_R", [-16000, -5800, -98], [40, 1.8, 0.06], MATS["cyan"])

    for i in range(7):
        x = -17800 + i * 600
        spawn_colored_mesh(f"SM_CORE_GMH_Arch_{i:02d}_L", [x, -8600, 520], [0.9, 0.9, 10], MATS["marble"])
        spawn_colored_mesh(f"SM_CORE_GMH_Arch_{i:02d}_R", [x, -5400, 520], [0.9, 0.9, 10], MATS["marble"])
        spawn_colored_mesh(f"SM_CORE_GMH_Arch_{i:02d}_Top", [x, -7000, 1040], [1.2, 34, 0.85], MATS["gold"])
        glass_mat = [MATS["gold"], MATS["violet"], MATS["teal"], MATS["crimson"]][i % 4]
        spawn_colored_mesh(
            f"SM_CORE_GMH_Glass_{i:02d}",
            [x, -7000, 800],
            [0.08, 10.2, 4.2],
            glass_mat,
            [0, 90, 0],
            PLANE,
        )

    for i in range(18):
        x = -18200 + i * 260
        y = -7600 + ((i % 6) * 240)
        z = 1580 + (i % 3) * 110
        shard_mat = [MATS["cyan"], MATS["violet"], MATS["teal"], MATS["gold"]][i % 4]
        spawn_colored_mesh(
            f"SM_CORE_GMH_Shard_{i:02d}",
            [x, y, z],
            [0.1, 0.9, 0.08],
            shard_mat,
            [18, (i * 27) % 360, 21],
        )

    spawn_light("L_CORE_GMH_01", "SpotLight", [-16600, -7000, 2000], [90, 0, 0], [1, 1, 1])
    spawn_light("L_CORE_GMH_02", "SpotLight", [-15200, -7000, 1900], [90, 0, 0], [1, 1, 1])

    # 4.2 System Dais Plaza (center).
    spawn_colored_mesh("SM_CORE_DAIS_Pool", [0, 0, -150], [36, 36, 0.15], MATS["cyan"], mesh=CYL)
    spawn_colored_mesh("SM_CORE_DAIS_Main", [0, 0, 15], [28, 28, 0.45], MATS["marble"], mesh=CYL)
    spawn_colored_mesh("SM_CORE_DAIS_InlayA", [0, 0, 40], [20, 0.35, 0.06], MATS["bronze"])
    spawn_colored_mesh("SM_CORE_DAIS_InlayB", [0, 0, 40], [0.35, 20, 0.06], MATS["bronze"])
    spawn_colored_mesh("SM_CORE_DAIS_InlayC", [0, 0, 40], [14, 0.25, 0.06], MATS["cyan"], [0, 45, 0])
    spawn_colored_mesh("SM_CORE_DAIS_InlayD", [0, 0, 40], [14, 0.25, 0.06], MATS["cyan"], [0, -45, 0])

    for i in range(14):
        a = (2.0 * math.pi * i) / 14.0
        x = 920 * math.cos(a)
        y = 920 * math.sin(a)
        yaw = math.degrees(a) + 90
        mat = MATS["gold"] if i % 2 == 0 else MATS["bronze"]
        spawn_colored_mesh(f"SM_CORE_DAIS_RingSeg_{i:02d}", [x, y, 840], [0.2, 2.0, 0.25], mat, [0, yaw, 0])
    spawn_colored_mesh("SM_CORE_DAIS_CrystalCore", [0, 0, 930], [3.6, 3.6, 10], MATS["cyan"], mesh=CONE)

    for i in range(4):
        a = (2.0 * math.pi * i) / 4.0
        x = 2900 * math.cos(a)
        y = 2900 * math.sin(a)
        spawn_colored_mesh(f"SM_CORE_DAIS_Bench_{i:02d}", [x, y, 80], [4.2, 1.5, 0.7], MATS["stone"])
        sx = 3500 * math.cos(a + 0.35)
        sy = 3500 * math.sin(a + 0.35)
        spawn_colored_mesh(f"SM_CORE_DAIS_Guardian_{i:02d}", [sx, sy, 410], [1.1, 1.1, 8.2], MATS["marble"])
        spawn_colored_mesh(f"SM_CORE_DAIS_Blade_{i:02d}", [sx, sy, 160], [0.2, 1.4, 2.6], MATS["iron"])

    # 4.3 Armory Pavilion (east).
    spawn_colored_mesh("SM_CORE_ARM_Floor", [12200, 0, -100], [52, 32, 0.28], MATS["marble"])
    for i in range(10):
        x = 10200 + i * 450
        spawn_colored_mesh(f"SM_CORE_ARM_Rack_{i:02d}", [x, -1200, 210], [0.2, 4.4, 2.7], MATS["bronze"])
    for i in range(6):
        x = 10600 + i * 700
        spawn_colored_mesh(f"SM_CORE_ARM_RelicPed_{i:02d}", [x, 1000, 120], [1.1, 1.1, 2.0], MATS["gold"], mesh=CYL)
        spawn_colored_mesh(f"SM_CORE_ARM_Blade_{i:02d}", [x, 1000, 420], [0.1, 1.2, 0.12], MATS["iron"], [0, i * 18, 25])
    for i in range(12):
        x = 10000 + i * 380
        spawn_colored_mesh(f"SM_CORE_ARM_Banner_{i:02d}", [x, 1550, 650], [0.08, 1.6, 4], MATS["crimson"], [0, 90, 0], PLANE)
    spawn_colored_mesh("SM_CORE_ARM_UpgradePed", [12200, -350, 130], [1.5, 1.5, 2.1], MATS["cyan"], mesh=CYL)

    # 4.4 Archive Rotunda (west).
    spawn_colored_mesh("SM_CORE_ARC_Base", [-12200, 0, -100], [44, 44, 0.25], MATS["stone"], mesh=CYL)
    spawn_colored_mesh("SM_CORE_ARC_Dome", [-12200, 0, 1380], [42, 42, 0.55], MATS["marble"], mesh=SPHERE)
    spawn_colored_mesh("SM_CORE_ARC_Oculus", [-12200, 0, 1840], [8, 8, 0.1], MATS["cyan"], mesh=CYL)
    for i in range(16):
        a = (2.0 * math.pi * i) / 16.0
        x = -12200 + 2800 * math.cos(a)
        y = 2800 * math.sin(a)
        spawn_colored_mesh(f"SM_CORE_ARC_Shelf_{i:02d}", [x, y, 290], [0.25, 5.6, 5], MATS["bronze"], [0, math.degrees(a), 0])
    for i in range(14):
        x = -14200 + i * 300
        spawn_colored_mesh(f"SM_CORE_ARC_Step_{i:02d}", [x, -400, -45 + i * 24], [1.8, 4.8, 0.25], MATS["marble"])
    spawn_colored_mesh("SM_CORE_ARC_ProjectionPed", [-12200, 0, 120], [1.8, 1.8, 2.4], MATS["cyan"], mesh=CYL)

    # 4.5 Ascension Gallery (north).
    spawn_colored_mesh("SM_CORE_ASC_Floor", [0, 12800, -100], [84, 38, 0.3], MATS["marble"])
    gate_x = [-4200, 0, 4200]
    gate_mats = [MATS["crimson"], MATS["teal"], MATS["bronze"]]
    for i, gx in enumerate(gate_x):
        spawn_colored_mesh(f"SM_CORE_ASC_Gate_{i+1}_PillarL", [gx - 850, 14600, 630], [1.2, 1.2, 12], MATS["marble"])
        spawn_colored_mesh(f"SM_CORE_ASC_Gate_{i+1}_PillarR", [gx + 850, 14600, 630], [1.2, 1.2, 12], MATS["marble"])
        spawn_colored_mesh(f"SM_CORE_ASC_Gate_{i+1}_Top", [gx, 14600, 1240], [1.4, 18, 1], MATS["gold"])
        spawn_colored_mesh(f"SM_CORE_ASC_Gate_{i+1}_Seal", [gx, 14700, 720], [6.2, 6.2, 0.1], gate_mats[i], [90, 0, 0], CYL)
        spawn_colored_mesh(f"SM_CORE_ASC_GuardL_{i+1}", [gx - 1800, 14100, 420], [1.0, 1.0, 8], MATS["stone"])
        spawn_colored_mesh(f"SM_CORE_ASC_GuardR_{i+1}", [gx + 1800, 14100, 420], [1.0, 1.0, 8], MATS["stone"])
        spawn_colored_mesh(f"SM_CORE_ASC_BladeL_{i+1}", [gx - 1800, 14100, 170], [0.18, 1.4, 2.4], MATS["iron"])
        spawn_colored_mesh(f"SM_CORE_ASC_BladeR_{i+1}", [gx + 1800, 14100, 170], [0.18, 1.4, 2.4], MATS["iron"])
        mosaic_mat = [MATS["iron"], MATS["teal"], MATS["bronze"]][i]
        spawn_colored_mesh(f"SM_CORE_ASC_Mosaic_{i+1}", [gx, 13350, -88], [8.2, 4.4, 0.04], mosaic_mat)

    # Core atmosphere lights.
    spawn_light("L_CORE_Key_01", "DirectionalLight", [-4200, -2600, 8600], [-45, 35, 0], [1, 1, 1])
    for i in range(10):
        a = (2.0 * math.pi * i) / 10.0
        x = 17000 * math.cos(a)
        y = 17000 * math.sin(a)
        spawn_light(f"L_CORE_Rim_{i:02d}", "PointLight", [x, y, 2300], None, [1, 1, 1])


def build_contract_terrace_and_vista() -> None:
    # 4.6 Contract Terrace (south).
    spawn_colored_mesh("SM_CON_TerraceDeck", [0, -13200, -92], [92, 44, 0.28], MATS["marble"])
    spawn_colored_mesh("SM_CON_Rail_N", [0, -10900, 170], [92, 0.4, 3.2], MATS["gold"])
    spawn_colored_mesh("SM_CON_Rail_S", [0, -15450, 170], [92, 0.4, 3.2], MATS["gold"])
    spawn_colored_mesh("SM_CON_Rail_E", [9200, -13200, 170], [0.4, 44, 3.2], MATS["gold"])
    spawn_colored_mesh("SM_CON_Rail_W", [-9200, -13200, 170], [0.4, 44, 3.2], MATS["gold"])

    for i in range(6):
        x = -6200 + i * 2400
        spawn_colored_mesh(f"SM_CON_Bench_{i:02d}", [x, -12100, 70], [2.8, 1.0, 0.7], MATS["stone"])

    # Telescope-like instrument.
    spawn_colored_mesh("SM_CON_Telescope_Base", [0, -13850, 130], [1.4, 1.4, 2.4], MATS["bronze"], mesh=CYL)
    spawn_colored_mesh("SM_CON_Telescope_Body", [0, -14200, 560], [0.42, 0.42, 4.8], MATS["gold"], [35, 0, 0], CYL)

    # Vista vertical tower descending below cloud layer.
    for i in range(10):
        z = -1800 - i * 4200
        spawn_colored_mesh(f"SM_CON_VistaTower_{i:02d}", [0, -68000, z], [12, 12, 20], MATS["iron"], mesh=CYL)
        if i % 2 == 0:
            spawn_colored_mesh(f"SM_CON_VistaBeacon_{i:02d}", [0, -68000, z + 1700], [0.6, 0.6, 0.6], MATS["cyan"], mesh=SPHERE)

    # Dust/faint lights in the void.
    for i in range(40):
        x = -2500 + (i % 10) * 520
        y = -65000 - (i // 10) * 1700
        z = -3000 - (i % 7) * 950
        mat = MATS["cyan"] if i % 3 == 0 else MATS["stone"]
        spawn_colored_mesh(f"SM_CON_VoidDust_{i:02d}", [x, y, z], [0.08, 0.08, 0.08], mat, mesh=SPHERE)

    spawn_light("L_CON_SkylineWarm", "SpotLight", [0, -10000, 5000], [45, 180, 0], [1, 1, 1])
    spawn_light("L_CON_VistaCool", "SpotLight", [0, -18000, 4200], [30, 0, 0], [1, 1, 1])


def build_signal_quarter() -> None:
    # 5.x Signal Quarter (NE).
    spawn_colored_mesh("SM_SIG_QuarterPlate", [18000, 17000, -100], [80, 70, 0.22], MATS["stone"])

    # Signal Tower (60m).
    spawn_colored_mesh("SM_SIG_Tower_Core", [19800, 18800, 2900], [6.2, 6.2, 58], MATS["marble"])
    for i in range(6):
        a = (2.0 * math.pi * i) / 6.0
        x = 19800 + 920 * math.cos(a)
        y = 18800 + 920 * math.sin(a)
        spawn_colored_mesh(f"SM_SIG_Tower_Rib_{i:02d}", [x, y, 2900], [0.6, 0.6, 58], MATS["bronze"])
    for i in range(10):
        z = 500 + i * 540
        spawn_colored_mesh(f"SM_SIG_Tower_Conduit_{i:02d}", [20520, 18800, z], [0.14, 0.14, 2.8], MATS["cyan"])
    for i in range(8):
        a = (2.0 * math.pi * i) / 8.0
        x = 19800 + 1400 * math.cos(a)
        y = 18800 + 1400 * math.sin(a)
        spawn_colored_mesh(
            f"SM_SIG_Tower_Antenna_{i:02d}",
            [x, y, 6200],
            [0.18, 2.1, 0.22],
            MATS["cyan"] if i % 2 == 0 else MATS["gold"],
            [0, math.degrees(a), 0],
        )

    # Relay Station.
    spawn_colored_mesh("SM_SIG_Relay_Base", [15200, 17000, 90], [34, 24, 2.0], MATS["marble"])
    for i in range(12):
        x = 14400 + (i % 6) * 320
        y = 16200 + (i // 6) * 1600
        spawn_colored_mesh(f"SM_SIG_Relay_Crystal_{i:02d}", [x, y, 530], [0.35, 0.35, 1.2], MATS["cyan"], [0, i * 30, 20], CONE)

    # Monitoring Hall.
    spawn_colored_mesh("SM_SIG_Monitor_Base", [21400, 16000, 120], [40, 14, 2.4], MATS["stone"])
    spawn_colored_mesh("SM_SIG_Monitor_TransWall", [21400, 17380, 640], [38, 0.12, 6], MATS["cyan"])
    for i in range(16):
        x = 19800 + i * 200
        spawn_colored_mesh(f"SM_SIG_Monitor_DataBand_{i:02d}", [x, 17360, 560 + (i % 4) * 110], [0.8, 0.04, 0.35], MATS["teal"])

    # Waveform Bridge to core.
    for i in range(16):
        t = i / 15.0
        x = 9000 + t * 8000
        y = 9000 + t * 6000
        z = -90 + math.sin(t * math.pi) * 120
        spawn_colored_mesh(f"SM_SIG_WaveBridge_{i:02d}", [x, y, z], [3.4, 1.2, 0.22], MATS["marble"])
        spawn_colored_mesh(f"SM_SIG_WaveBridge_RailL_{i:02d}", [x - 40, y - 120, z + 150], [0.08, 0.6, 2.0], MATS["gold"])
        spawn_colored_mesh(f"SM_SIG_WaveBridge_RailR_{i:02d}", [x + 40, y + 120, z + 150], [0.08, 0.6, 2.0], MATS["gold"])
        if i % 2 == 0:
            spawn_colored_mesh(f"SM_SIG_WaveParticle_{i:02d}", [x, y, z + 320], [0.12, 0.12, 0.12], MATS["cyan"], mesh=SPHERE)

    spawn_light("L_SIG_TowerGlow", "PointLight", [19800, 18800, 5200], None, [1, 1, 1])
    spawn_light("L_SIG_BridgeFill", "SpotLight", [13000, 12400, 3000], [80, -130, 0], [1, 1, 1])


def build_skyline_and_residential() -> None:
    # 6) Residential terraces backdrop (south/east).
    tiers = [
        (11000, -25000, 60, 6),
        (14500, -31000, -200, 6),
        (17800, -37000, -460, 6),
    ]
    for ti, (x0, y0, z0, n) in enumerate(tiers):
        for i in range(n):
            x = x0 + i * 1900
            y = y0 - (i % 2) * 1200
            spawn_colored_mesh(f"SM_RES_Block_{ti}_{i:02d}", [x, y, z0 + 650], [8.0, 6.0, 13], MATS["marble"])
            spawn_colored_mesh(f"SM_RES_Balcony_{ti}_{i:02d}", [x, y + 420, z0 + 320], [2.4, 0.45, 0.35], MATS["gold"])
            spawn_colored_mesh(f"SM_RES_RooftopGarden_{ti}_{i:02d}", [x, y, z0 + 1320], [3.2, 2.4, 0.15], MATS["teal"])

    spawn_colored_mesh("SM_RES_ResonanceChapel_Base", [23000, -29000, 700], [9, 9, 9], MATS["marble"], mesh=CYL)
    spawn_colored_mesh("SM_RES_ResonanceChapel_Dome", [23000, -29000, 1700], [8, 8, 0.55], MATS["stone"], mesh=SPHERE)
    spawn_colored_mesh("SM_RES_ResonanceChapel_Orb", [23000, -29000, 2600], [1.0, 1.0, 1.0], MATS["cyan"], mesh=SPHERE)
    spawn_colored_mesh("SM_RES_GardenCascade", [25200, -31800, 760], [5, 5, 13], MATS["teal"], mesh=CYL)
    spawn_colored_mesh("SM_RES_MerchantRow", [26800, -28400, 360], [20, 6, 5], MATS["bronze"])

    # 7) Skyline civic spires ring.
    random.seed(301)
    east_positions = [(30000, -5000), (32000, 2000), (34000, 9000), (31000, 15000), (33500, 22000)]
    west_positions = [(-30000, -7000), (-33000, 1000), (-35000, 8500), (-31000, 16000), (-34000, 23500)]
    sig_positions = [(25000, 21000), (27000, 26000), (23000, 27000)]
    all_pos = east_positions + west_positions + sig_positions
    for i, (x, y) in enumerate(all_pos):
        h_scale = random.choice([26, 32, 40, 52, 68, 80])
        spawn_colored_mesh(f"SM_SKY_Spire_{i:02d}", [x, y, h_scale * 50], [4.6, 4.6, h_scale], MATS["marble"])
        spawn_colored_mesh(f"SM_SKY_Rib_{i:02d}", [x + 320, y, h_scale * 50], [0.6, 0.6, h_scale], MATS["gold"])
        spawn_colored_mesh(f"SM_SKY_Crown_{i:02d}", [x, y, h_scale * 100 + 320], [1.2, 1.2, 0.45], MATS["cyan"], mesh=CYL)

    for i in range(22):
        a = (2.0 * math.pi * i) / 22.0
        x = 38000 * math.cos(a)
        y = 38000 * math.sin(a)
        z = 1400 + (i % 5) * 250
        spawn_colored_mesh(f"SM_CLOUD_Silhouette_{i:02d}", [x, y, z], [10, 10, 0.8], MATS["stone"], mesh=SPHERE)


def build_transit_and_vehicles() -> None:
    # 8) Transit boulevards and visual-only vehicles.
    spawn_colored_mesh("SM_TRN_Lane_East", [13000, 2500, -95], [70, 4, 0.12], MATS["marble"])
    spawn_colored_mesh("SM_TRN_Lane_West", [-13000, -2500, -95], [70, 4, 0.12], MATS["marble"])
    spawn_colored_mesh("SM_TRN_Conduit_East", [13000, 2900, -80], [70, 0.2, 0.04], MATS["cyan"])
    spawn_colored_mesh("SM_TRN_Conduit_West", [-13000, -2900, -80], [70, 0.2, 0.04], MATS["cyan"])

    # Docking pads.
    pads = [(10800, 2600, 20), (15200, 9800, 20), (14800, 15000, 20)]
    for i, (x, y, z) in enumerate(pads):
        spawn_colored_mesh(f"SM_TRN_DockPad_{i:02d}", [x, y, z], [4.2, 4.2, 0.2], MATS["cyan"], mesh=CYL)
        spawn_colored_mesh(f"SM_TRN_DockRim_{i:02d}", [x, y, z + 30], [4.8, 4.8, 0.08], MATS["gold"], mesh=CYL)

    # Hover skiffs.
    skiffs = [(11100, 2850, 120), (11600, 2400, 120), (15000, 15500, 120)]
    for i, (x, y, z) in enumerate(skiffs):
        spawn_colored_mesh(f"SM_VEH_HoverSkiff_Body_{i:02d}", [x, y, z], [1.7, 0.8, 0.25], MATS["marble"])
        spawn_colored_mesh(f"SM_VEH_HoverSkiff_Under_{i:02d}", [x, y, z - 60], [1.3, 0.5, 0.08], MATS["cyan"])

    # Courier pods cluster.
    for i in range(7):
        x = 10200 + i * 230
        y = 2100 + (i % 2) * 180
        spawn_colored_mesh(f"SM_VEH_CourierPod_{i:02d}", [x, y, 90], [0.45, 0.45, 1.2], MATS["teal"], mesh=CYL)

    # Cargo sleds near relay and armory.
    sleds = [(14500, 16400, 90), (14900, 16400, 90), (10900, -900, 90)]
    for i, (x, y, z) in enumerate(sleds):
        spawn_colored_mesh(f"SM_VEH_CargoSled_{i:02d}", [x, y, z], [1.9, 0.85, 0.14], MATS["iron"])
        spawn_colored_mesh(f"SM_VEH_CargoRail_{i:02d}", [x, y, z + 35], [1.5, 0.06, 0.22], MATS["bronze"])

    # Transit gate arches.
    gates = [(9000, 6800), (13500, 11500), (17500, 16500)]
    for i, (x, y) in enumerate(gates):
        spawn_colored_mesh(f"SM_TRN_Gate_{i:02d}_L", [x - 550, y, 430], [0.5, 0.5, 8.4], MATS["marble"])
        spawn_colored_mesh(f"SM_TRN_Gate_{i:02d}_R", [x + 550, y, 430], [0.5, 0.5, 8.4], MATS["marble"])
        spawn_colored_mesh(f"SM_TRN_Gate_{i:02d}_Top", [x, y, 860], [0.6, 12, 0.5], MATS["cyan"])


def build_arenas_outskirts() -> None:
    # 9.1 Battle Arena (NW).
    spawn_colored_mesh("SM_ARENA_Battle_Base", [-16200, 12200, -90], [46, 46, 0.25], MATS["marble"], mesh=CYL)
    spawn_colored_mesh("SM_ARENA_Battle_Ring", [-16200, 12200, 40], [34, 34, 0.08], MATS["cyan"], mesh=CYL)
    for i in range(10):
        r = 4200 + i * 220
        spawn_colored_mesh(f"SM_ARENA_Battle_Step_{i:02d}", [-16200, 12200, 40 + i * 40], [r / 100, r / 100, 0.05], MATS["stone"], mesh=CYL)
    for i in range(8):
        x = -18400 + i * 630
        spawn_colored_mesh(f"SM_ARENA_Battle_Dummy_{i:02d}", [x, 11200, 260], [0.7, 0.7, 4.6], MATS["bronze"])

    # 9.2 PK Arena (NE edge).
    spawn_colored_mesh("SM_ARENA_PK_HallFloor", [15400, 9000, -90], [58, 26, 0.25], MATS["marble"])
    spawn_colored_mesh("SM_ARENA_PK_Court", [15400, 9000, -70], [34, 12, 0.08], MATS["iron"])
    spawn_colored_mesh("SM_ARENA_PK_Channel_L", [15400, 10100, -66], [34, 0.7, 0.05], MATS["cyan"])
    spawn_colored_mesh("SM_ARENA_PK_Channel_R", [15400, 7900, -66], [34, 0.7, 0.05], MATS["cyan"])
    for i in range(11):
        x = 13700 + i * 340
        spawn_colored_mesh(f"SM_ARENA_PK_Lattice_{i:02d}", [x, 11400, 820], [0.12, 0.08, 10.6], MATS["cyan"])
    spawn_colored_mesh("SM_ARENA_PK_Podium_A", [14100, 9000, 45], [1.2, 1.2, 0.35], MATS["cyan"], mesh=CYL)
    spawn_colored_mesh("SM_ARENA_PK_Podium_B", [16700, 9000, 45], [1.2, 1.2, 0.35], MATS["cyan"], mesh=CYL)

    # 10) Outskirts perimeter (east + southeast).
    spawn_colored_mesh("SM_OUT_Perimeter_East", [26000, 6000, -120], [65, 45, 0.2], MATS["stone"])
    spawn_colored_mesh("SM_OUT_Perimeter_SE", [22000, -15500, -120], [70, 50, 0.2], MATS["stone"])

    for i in range(16):
        x = 23000 + (i % 8) * 950
        y = -16800 + (i // 8) * 2200
        z = 180 + (i % 3) * 80
        spawn_colored_mesh(f"SM_OUT_BrokenColumn_{i:02d}", [x, y, z], [0.5, 0.5, 2.8], MATS["iron"])
        if i % 2 == 0:
            spawn_colored_mesh(f"SM_OUT_Shrub_{i:02d}", [x + 210, y - 120, -30], [0.8, 0.8, 0.6], MATS["teal"], mesh=SPHERE)

    # Spawn clearings / future monster staging shells.
    clearings = [(24600, 5600), (28200, 8200), (24000, -14200), (19800, -17600)]
    for i, (x, y) in enumerate(clearings):
        spawn_colored_mesh(f"SM_OUT_SpawnClearing_{i:02d}", [x, y, -102], [12, 8, 0.06], MATS["iron"])
        spawn_colored_mesh(f"SM_OUT_WarningRing_{i:02d}", [x, y, -90], [13.5, 9.5, 0.03], MATS["cyan"])

    spawn_light("L_OUT_FogEdge_01", "PointLight", [25000, 5000, 1200], None, [1, 1, 1])
    spawn_light("L_OUT_FogEdge_02", "PointLight", [22000, -15000, 1200], None, [1, 1, 1])


def build_undercroft_stretch() -> None:
    # 11) Undercroft transition below ascension.
    spawn_colored_mesh("SM_UND_DescentPad", [0, 11800, -2400], [18, 18, 0.2], MATS["iron"], mesh=CYL)
    spawn_colored_mesh("SM_UND_Railing_N", [0, 12800, -2200], [18, 0.2, 2.4], MATS["bronze"])
    spawn_colored_mesh("SM_UND_Railing_S", [0, 10800, -2200], [18, 0.2, 2.4], MATS["bronze"])
    spawn_colored_mesh("SM_UND_Railing_E", [1800, 11800, -2200], [0.2, 18, 2.4], MATS["bronze"])
    spawn_colored_mesh("SM_UND_Railing_W", [-1800, 11800, -2200], [0.2, 18, 2.4], MATS["bronze"])

    for i in range(12):
        x = -2600 + i * 470
        spawn_colored_mesh(f"SM_UND_Chain_{i:02d}", [x, 11800, -1750], [0.05, 0.05, 6.0], MATS["iron"], mesh=CYL)

    # Old archives shell.
    spawn_colored_mesh("SM_UND_OldArchiveFloor", [0, 15200, -2450], [36, 16, 0.2], MATS["stone"])
    for i in range(10):
        x = -2600 + i * 570
        spawn_colored_mesh(f"SM_UND_Shelf_{i:02d}", [x, 15800, -2120], [0.2, 4.6, 3.2], MATS["iron"])
    spawn_colored_mesh("SM_UND_RestrictedPlaque_Back", [0, 14680, -2030], [7.0, 0.15, 2.0], MATS["bronze"])
    spawn_colored_mesh("SM_UND_RestrictedPlaque_Text", [0, 14695, -2030], [6.2, 0.04, 1.4], MATS["cyan"])


def place_markers_and_plaques() -> None:
    # Required markers with exact names.
    spawn_colored_mesh("BP_PlayerStart_Map_HubCitadelCity", [-18600, -7000, 120], [0.7, 0.7, 2.0], MATS["gold"], mesh=CYL)
    spawn_colored_mesh("BP_SafeNode_00", [1000, -1500, 120], [0.8, 0.8, 2.0], MATS["cyan"], mesh=CYL)
    spawn_colored_mesh("BP_AscensionGate_00", [-4200, 13800, 20], [1.4, 1.4, 0.35], MATS["cyan"], mesh=CYL)
    spawn_colored_mesh("BP_AscensionGate_01", [0, 13800, 20], [1.4, 1.4, 0.35], MATS["cyan"], mesh=CYL)
    spawn_colored_mesh("BP_AscensionGate_02", [4200, 13800, 20], [1.4, 1.4, 0.35], MATS["cyan"], mesh=CYL)

    # 8 core plaques as requested.
    plaque_locs = [
        (-4500, -2300, 130),
        (-1900, -2800, 130),
        (1900, -2800, 130),
        (4500, -2300, 130),
        (-5200, 1900, 130),
        (5200, 1900, 130),
        (-200, -12100, 150),
        (200, 12100, 150),
    ]
    for i, (x, y, z) in enumerate(plaque_locs, start=1):
        name = f"BP_SystemNoticePlaque_{i:02d}"
        spawn_colored_mesh(name, [x, y, z], [0.9, 0.2, 2.1], MATS["bronze"])
        spawn_colored_mesh(f"SM_CORE_PlaqueFace_{i:02d}", [x + 10, y + 16, z + 10], [0.72, 0.04, 1.32], MATS["cyan"])

    # Core contextual plaques around outskirts warnings (visual only).
    warnings = [
        (24800, 5200, 160),
        (28200, 8500, 160),
        (23600, -14500, 160),
    ]
    for i, (x, y, z) in enumerate(warnings, start=9):
        name = f"BP_SystemNoticePlaque_{i:02d}"
        spawn_colored_mesh(name, [x, y, z], [0.85, 0.2, 2.0], MATS["iron"])
        spawn_colored_mesh(f"SM_OUT_PlaqueFace_{i:02d}", [x + 8, y + 14, z + 12], [0.68, 0.04, 1.2], MATS["cyan"])


def main() -> int:
    global overwrite_existing
    parser = argparse.ArgumentParser(description="Build SignalBound metropolis hub in current level.")
    parser.add_argument(
        "--phase",
        choices=[
            "all",
            "clear",
            "core",
            "contract_vista",
            "signal_quarter",
            "skyline",
            "vehicles",
            "arenas_outskirts",
            "undercroft",
            "markers_plaques",
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
    parser.add_argument("--seed", type=int, default=20260301)
    args = parser.parse_args()

    random.seed(args.seed)
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
        removed = clear_existing_hub()
        print(f"PHASE_DONE=clear_removed_{removed}", flush=True)
    if phase in ("all", "core"):
        build_sovereign_core()
        print("PHASE_DONE=build_sovereign_core", flush=True)
    if phase in ("all", "contract_vista"):
        build_contract_terrace_and_vista()
        print("PHASE_DONE=build_contract_terrace_and_vista", flush=True)
    if phase in ("all", "signal_quarter"):
        build_signal_quarter()
        print("PHASE_DONE=build_signal_quarter", flush=True)
    if phase in ("all", "skyline"):
        build_skyline_and_residential()
        print("PHASE_DONE=build_skyline_and_residential", flush=True)
    if phase in ("all", "vehicles"):
        build_transit_and_vehicles()
        print("PHASE_DONE=build_transit_and_vehicles", flush=True)
    if phase in ("all", "arenas_outskirts"):
        build_arenas_outskirts()
        print("PHASE_DONE=build_arenas_outskirts", flush=True)
    if phase in ("all", "undercroft"):
        build_undercroft_stretch()
        print("PHASE_DONE=build_undercroft_stretch", flush=True)
    if phase in ("all", "markers_plaques"):
        place_markers_and_plaques()
        print("PHASE_DONE=place_markers_and_plaques", flush=True)

    print(f"SPAWNED_COUNT={len(spawned)}")
    print(f"SKIPPED_EXISTING_COUNT={skipped_existing}")
    print(f"MATERIAL_APPLICATIONS={materials_applied}")
    if failed:
        print(f"FAILED_COUNT={len(failed)}")
        for name, err in failed[:40]:
            print(f"FAILED {name}: {err}")
    else:
        print("FAILED_COUNT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
