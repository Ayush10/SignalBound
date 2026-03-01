#!/usr/bin/env python3
"""Add vibrant color and floral beautification pass to Map_HubCitadelCity."""

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
    "gold": "/Game/ThirdPerson/MI_ThirdPersonColWay.MI_ThirdPersonColWay",
    "rose_red": "/Game/Variant_Combat/Materials/M_Lava.M_Lava",
    "pink": "/Game/Characters/Mannequins/Materials/Quinn/MI_Quinn_02.MI_Quinn_02",
    "violet": "/Game/Characters/Mannequins/Materials/Quinn/MI_Quinn_01.MI_Quinn_01",
    "cream": "/Game/Characters/Mannequins/Materials/Manny/MI_Manny_01_New.MI_Manny_01_New",
    "emerald": "/Game/Characters/Mannequins/Materials/Manny/MI_Manny_02_New.MI_Manny_02_New",
    "azure": "/Game/LevelPrototyping/Materials/MI_DefaultColorway.MI_DefaultColorway",
}

ROSE_VARIANTS = [
    "CathedralWinchester",
    "SunflareRose",
    "IvoryLumin",
    "AuroraVelvet",
]

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


def delete_if_exists(name: str) -> None:
    send("delete_actor", {"name": name})


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


def apply_material(actor_name: str, material_path: str) -> bool:
    global materials_applied
    resp = send(
        "apply_material_to_actor",
        {"actor_name": actor_name, "material_path": material_path, "material_slot": 0},
    )
    if is_ok(resp):
        materials_applied += 1
        return True
    failed.append((f"mat:{actor_name}", resp.get("error", str(resp))))
    return False


def recolor_by_pattern(pattern: str, material_cycle: List[str]) -> int:
    found = send("find_actors_by_name", {"pattern": pattern})
    if not is_ok(found):
        return 0

    names = sorted(actor.get("name", "") for actor in found.get("result", {}).get("actors", []))
    names = [n for n in names if n]
    count = 0
    for idx, name in enumerate(names):
        mat = material_cycle[idx % len(material_cycle)]
        if apply_material(name, mat):
            count += 1
    return count


def create_ribbon_row(row_name: str, x_start: float, x_step: float, y: float, z: float, count: int) -> None:
    mats = [MATS["pink"], MATS["violet"], MATS["azure"], MATS["gold"], MATS["cream"]]
    for i in range(count):
        name = f"SM_GARDEN_Ribbon_{row_name}_{i:02d}"
        x = x_start + x_step * i
        yaw = 0 if row_name == "Hall" else 90
        if spawn_mesh(name, [x, y, z], [0.1, 5.0, 1.7], [0, yaw, 8], mesh=PLANE):
            apply_material(name, mats[i % len(mats)])


def create_flower_cluster(cluster_idx: int, x: float, y: float, z: float) -> None:
    random.seed(1000 + cluster_idx)

    planter = f"SM_GARDEN_Planter_{cluster_idx:02d}"
    if spawn_mesh(planter, [x, y, z], [2.2, 2.2, 0.7], mesh=CYL):
        apply_material(planter, MATS["gold"])

    soil = f"SM_GARDEN_Soil_{cluster_idx:02d}"
    if spawn_mesh(soil, [x, y, z + 35], [1.9, 1.9, 0.2], mesh=CYL):
        apply_material(soil, MATS["emerald"])

    bloom_mats = [MATS["rose_red"], MATS["pink"], MATS["cream"], MATS["violet"]]
    for j in range(8):
        a = (2.0 * math.pi * j) / 8.0
        r = 90 + (j % 3) * 18
        sx = x + r * math.cos(a)
        sy = y + r * math.sin(a)
        stem_h = 1.25 + (j % 3) * 0.18
        rose_kind = ROSE_VARIANTS[j % len(ROSE_VARIANTS)]

        stem = f"SM_FLOWER_Stem_{cluster_idx:02d}_{j:02d}"
        if spawn_mesh(stem, [sx, sy, z + 110], [0.08, 0.08, stem_h], mesh=CYL):
            apply_material(stem, MATS["emerald"])

        bloom = f"SM_Rose_{rose_kind}_{cluster_idx:02d}_{j:02d}"
        if spawn_mesh(bloom, [sx, sy, z + 110 + (stem_h * 100)], [0.24, 0.24, 0.24], mesh=SPHERE):
            apply_material(bloom, bloom_mats[j % len(bloom_mats)])

        bud = f"SM_FLOWER_Bud_{cluster_idx:02d}_{j:02d}"
        if spawn_mesh(bud, [sx + 10, sy - 10, z + 95 + (stem_h * 100)], [0.11, 0.11, 0.18], [20, j * 37, 0], mesh=CONE):
            apply_material(bud, bloom_mats[(j + 1) % len(bloom_mats)])

    glow = f"L_BEAUTY_GardenGlow_{cluster_idx:02d}"
    spawn_light(glow, "PointLight", [x, y, z + 220], None, [0.7, 0.7, 0.7])


def beautify_hub(refresh_existing: bool) -> Dict[str, int]:
    removed = 0
    if refresh_existing:
        removed += delete_by_pattern("SM_GARDEN_")
        removed += delete_by_pattern("SM_FLOWER_")
        removed += delete_by_pattern("SM_Rose_")
        removed += delete_by_pattern("L_BEAUTY_")

    recolored = 0
    recolored += recolor_by_pattern("SM_GMH_Glass_", [MATS["pink"], MATS["violet"], MATS["azure"], MATS["gold"]])
    recolored += recolor_by_pattern("SM_GMH_Shards_", [MATS["cream"], MATS["pink"], MATS["violet"]])
    recolored += recolor_by_pattern("SM_SD_RingSeg_", [MATS["gold"], MATS["pink"], MATS["violet"], MATS["azure"]])
    recolored += recolor_by_pattern("SM_SD_Crystal_Core", [MATS["rose_red"]])
    recolored += recolor_by_pattern("SM_AG_Door_00_Seal", [MATS["rose_red"]])
    recolored += recolor_by_pattern("SM_AG_Door_01_Seal", [MATS["violet"]])
    recolored += recolor_by_pattern("SM_AG_Door_02_Seal", [MATS["azure"]])
    recolored += recolor_by_pattern("SM_EXT_Canal_", [MATS["azure"]])
    recolored += recolor_by_pattern("SM_VISTA_Dust_", [MATS["cream"], MATS["violet"]])

    create_ribbon_row("Hall", -13800, 1400, -1400, 1250, 10)
    create_ribbon_row("Terrace", 14800, 800, 6200, 1650, 9)

    # 12 lush flower clusters distributed around hero traversal path.
    clusters = [
        (-13200, -2350, 0),
        (-11200, -2350, 0),
        (-9200, -2350, 0),
        (-7200, 2350, 0),
        (-5200, 2350, 0),
        (-2400, 2200, 0),
        (1800, 2300, 0),
        (3800, -8400, 0),
        (6800, -8400, 0),
        (11200, -1500, 0),
        (11200, 1500, 0),
        (17800, 5200, 1300),
    ]
    for idx, (x, y, z) in enumerate(clusters):
        create_flower_cluster(idx, x, y, z)

    # Floral arch accents near entry and gallery.
    arch_points = [(-11800, 0, 820), (12400, -3600, 740), (12400, 3600, 740)]
    arch_mats = [MATS["pink"], MATS["violet"], MATS["gold"]]
    for i, (x, y, z) in enumerate(arch_points):
        for side in (-1, 1):
            name = f"SM_GARDEN_ArchBloom_{i:02d}_{'L' if side < 0 else 'R'}"
            if spawn_mesh(name, [x, y + (side * 380), z], [0.42, 0.42, 0.42], mesh=SPHERE):
                apply_material(name, arch_mats[(i + (0 if side < 0 else 1)) % len(arch_mats)])

    return {"removed": removed, "recolored": recolored}


def main() -> int:
    global overwrite_existing
    parser = argparse.ArgumentParser(description="Vibrant beautification pass for SignalBound hub.")
    parser.add_argument("--seed", type=int, default=20260301)
    parser.add_argument(
        "--refresh-existing",
        action="store_true",
        help="Delete old beauty actors before placing new ones.",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Replace actors with matching names instead of preserving them.",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    overwrite_existing = args.overwrite_existing

    if not is_ok(send("ping", {})):
        print("ERROR: Unreal MCP ping failed")
        return 2

    # Confirm hub exists before beautification.
    hub_check = send("find_actors_by_name", {"pattern": "SM_GMH_"})
    hub_count = len(hub_check.get("result", {}).get("actors", [])) if is_ok(hub_check) else 0
    if hub_count == 0:
        print("ERROR: Hub actors not found in current level. Load Map_HubCitadelCity first.")
        return 3

    stats = beautify_hub(refresh_existing=args.refresh_existing)

    print(f"HUB_BASE_COUNT={hub_count}")
    print(f"REMOVED_OLD_BEAUTY={stats['removed']}")
    print(f"RECOLORED_ACTORS={stats['recolored']}")
    print(f"SPAWNED_BEAUTY_ACTORS={len(spawned)}")
    print(f"SKIPPED_EXISTING_COUNT={skipped_existing}")
    print(f"MATERIAL_APPLICATIONS={materials_applied}")
    if failed:
        print(f"FAILED_COUNT={len(failed)}")
        for name, err in failed[:30]:
            print(f"FAILED {name}: {err}")
    else:
        print("FAILED_COUNT=0")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
