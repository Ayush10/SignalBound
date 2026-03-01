#!/usr/bin/env python3
"""Apply a Luminarch-aligned additive palette pass to existing environment maps.

This script does not delete actors. It only:
- Reassigns materials on existing static mesh actors.
- Tunes existing light properties for intended mood/readability.
"""

from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class MCPClient:
    host: str = "127.0.0.1"
    port: int = 55557
    throttle_s: float = 0.02

    def send(self, command_type: str, params: Optional[Dict[str, Any]] = None, timeout: float = 60.0) -> Dict[str, Any]:
        payload = {"type": command_type, "params": params or {}}
        encoded = json.dumps(payload).encode("utf-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        time.sleep(self.throttle_s)
        try:
            sock.connect((self.host, self.port))
            sock.sendall(encoded)
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


def ok(resp: Dict[str, Any]) -> bool:
    if not resp:
        return False
    if resp.get("status") == "error":
        return False
    if resp.get("success") is False:
        return False
    return True


def err_text(resp: Dict[str, Any]) -> str:
    if not resp:
        return "no response"
    if "error" in resp:
        return str(resp.get("error"))
    return str(resp)


MATS: Dict[str, str] = {
    # Palette approximation using available project materials.
    "ivory": "/Game/LevelPrototyping/Materials/MI_DefaultColorway.MI_DefaultColorway",
    "limestone": "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray_02.MI_PrototypeGrid_Gray_02",
    "gold": "/Game/ThirdPerson/MI_ThirdPersonColWay.MI_ThirdPersonColWay",
    "bronze": "/Game/Characters/Mannequins/Materials/Manny/MI_Manny_01_New.MI_Manny_01_New",
    "cyan": "/Game/Characters/Mannequins/Materials/Quinn/MI_Quinn_01.MI_Quinn_01",
    "indigo": "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark.MI_PrototypeGrid_TopDark",
    "foliage": "/Game/Characters/Mannequins/Materials/Manny/MI_Manny_02_New.MI_Manny_02_New",
    "water": "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray",
}


def load_level(c: MCPClient, map_path: str) -> None:
    resp = c.send("load_level", {"map_path": map_path})
    if not ok(resp):
        raise RuntimeError(f"Failed to load {map_path}: {err_text(resp)}")


def save_level(c: MCPClient) -> None:
    resp = c.send("save_current_level", {})
    if not ok(resp):
        raise RuntimeError(f"Failed to save current level: {err_text(resp)}")


def get_actors(c: MCPClient, name_contains: str) -> List[Dict[str, Any]]:
    resp = c.send("get_actors_in_level", {"name_contains": name_contains, "max_results": 0})
    if not ok(resp):
        return []
    result = resp.get("result") or {}
    return result.get("actors") or []


def apply_material(c: MCPClient, actor_name: str, material_path: str) -> bool:
    resp = c.send(
        "apply_material_to_actor",
        {"actor_name": actor_name, "material_path": material_path, "material_slot": 0},
    )
    return ok(resp)


def classify_hub_material(actor_name: str) -> Optional[str]:
    name = actor_name

    # Base districts.
    if name.startswith(("SM_CORE_", "SM_GMH_", "SM_SD_", "SM_AA_", "SM_AG_", "SM_EXT_", "SM_VISTA_")):
        material = MATS["ivory"]
    elif name.startswith(("SM_SIG_", "SM_CON_", "SM_TRN_", "SM_ARENA_", "SM_RES_", "SM_SKY_")):
        material = MATS["ivory"]
    elif name.startswith(("SM_OUT_", "SM_UND_", "SM_CLOUD_")):
        material = MATS["limestone"]
    elif name.startswith(("SM_GARDEN_", "SM_FLOWER_", "SM_Rose_")):
        material = MATS["foliage"]
    else:
        return None

    # Water / reflective floor accents.
    if any(k in name for k in ("_Pool", "_Canal_", "Mirror", "Water")):
        material = MATS["water"]

    # Cyan authority accents.
    if any(
        k in name
        for k in (
            "_CyanConduit_",
            "_Conduit_",
            "_Channel_",
            "_Crystal",
            "_Oculus",
            "_Seal",
            "_Glow",
            "_Beacon_",
            "_DataBand_",
            "_WaveParticle_",
            "_DockPad_",
            "_PlaqueFace_",
            "_TransWall",
        )
    ):
        material = MATS["cyan"]

    # Gold trims.
    if any(
        k in name
        for k in (
            "_Top",
            "_Rail_",
            "_Rib_",
            "_Crown_",
            "_RingSeg_",
            "_Rim_",
            "_Balcony_",
            "_RelicPed_",
            "_DoorPad_",
            "_WaveBridge_Rail",
            "_Telescope_Body",
        )
    ):
        material = MATS["gold"]

    # Bronze accents.
    if any(
        k in name
        for k in (
            "_Blade",
            "_Rack_",
            "_Shelf_",
            "_WeaponRack_",
            "_BookStack_",
            "_ScrollTube_",
            "_CargoRail_",
            "_BrokenColumn_",
            "_Guardian_",
            "_Chain_",
            "_MerchantRow",
        )
    ):
        material = MATS["bronze"]

    # Dark indigo mood for deep outskirts/void.
    if any(
        k in name
        for k in (
            "_VoidDust_",
            "PK_Court",
            "DescentPad",
            "OldArchiveFloor",
            "Silhouette_",
        )
    ):
        material = MATS["indigo"]

    # Silver-green foliage accents.
    if any(k in name for k in ("_RooftopGarden_", "_Shrub_", "SM_GARDEN_", "SM_FLOWER_", "SM_Rose_")):
        material = MATS["foliage"]

    return material


def classify_floor01_material(actor_name: str) -> Optional[str]:
    name = actor_name
    if not name.startswith("F1_"):
        return None
    if "_Wall_" in name or "BrokenWall" in name:
        return MATS["indigo"]
    if "_Floor" in name or "_Ceiling" in name or "_Pillar_" in name:
        return MATS["limestone"]
    if "FogCard" in name:
        return MATS["indigo"]
    if "Shaft_Dust_" in name:
        return MATS["water"]
    return None


def light_payload_hub(actor_name: str, actor_class: str) -> Optional[Dict[str, Any]]:
    name = actor_name
    is_point = actor_class == "PointLight"
    is_spot = actor_class == "SpotLight"
    is_dir = actor_class == "DirectionalLight"

    payload: Dict[str, Any] = {"name": name, "cast_shadows": True}

    if name.startswith(("L_CON_VistaCool", "L_SIG_", "L_SKY_", "L_OUT_")) or "Heartbeat" in name:
        payload["light_color"] = [0.27, 0.90, 1.0]
        payload["use_temperature"] = False
        if is_point:
            payload["intensity"] = 3000.0
        elif is_spot:
            payload["intensity"] = 9000.0
        elif is_dir:
            payload["intensity"] = 7.0
        return payload

    if name.startswith(("L_CORE_", "L_GMH_", "L_AA_", "L_AG_", "L_CON_SkylineWarm")):
        payload["light_color"] = [1.0, 0.94, 0.86]
        payload["use_temperature"] = True
        payload["temperature"] = 5300.0
        if is_point:
            payload["intensity"] = 2800.0
        elif is_spot:
            payload["intensity"] = 8500.0
        elif is_dir:
            payload["intensity"] = 7.5
        return payload

    return None


def light_payload_floor01(actor_name: str, actor_class: str) -> Optional[Dict[str, Any]]:
    name = actor_name
    is_point = actor_class == "PointLight"
    is_spot = actor_class == "SpotLight"
    is_dir = actor_class == "DirectionalLight"

    payload: Dict[str, Any] = {"name": name, "cast_shadows": True}

    if "Shaft_VoidGlow" in name:
        payload["light_color"] = [0.27, 0.90, 1.0]
        payload["use_temperature"] = False
        if is_point:
            payload["intensity"] = 2600.0
        return payload

    if "Key_" in name:
        payload["light_color"] = [0.74, 0.83, 0.96]
        payload["use_temperature"] = True
        payload["temperature"] = 6300.0
        if is_spot:
            payload["intensity"] = 9500.0
        return payload

    if name == "F1_Sun":
        payload["light_color"] = [0.85, 0.89, 0.96]
        payload["use_temperature"] = True
        payload["temperature"] = 6000.0
        if is_dir:
            payload["intensity"] = 7.0
        return payload

    return None


def run_hub_palette(c: MCPClient) -> Dict[str, int]:
    load_level(c, "/Game/Map_HubCitadelCity")

    applied = 0
    skipped = 0
    failed = 0
    seen: set[str] = set()

    for actor in get_actors(c, "SM_"):
        name = actor.get("name", "")
        if not name or name in seen:
            continue
        seen.add(name)

        actor_class = actor.get("class", "")
        if actor_class != "StaticMeshActor":
            continue

        material = classify_hub_material(name)
        if not material:
            skipped += 1
            continue

        if apply_material(c, name, material):
            applied += 1
        else:
            failed += 1

    marker_map = {
        "BP_PlayerStart_Map_HubCitadelCity": MATS["gold"],
        "BP_SafeNode_00": MATS["cyan"],
        "BP_AscensionGate_00": MATS["cyan"],
        "BP_AscensionGate_01": MATS["cyan"],
        "BP_AscensionGate_02": MATS["cyan"],
    }
    for name, material in marker_map.items():
        if apply_material(c, name, material):
            applied += 1
        else:
            skipped += 1

    lights_updated = 0
    for actor in get_actors(c, "L_"):
        name = actor.get("name", "")
        actor_class = actor.get("class", "")
        if "Light" not in actor_class:
            continue
        payload = light_payload_hub(name, actor_class)
        if not payload:
            continue
        resp = c.send("set_light_properties", payload)
        if ok(resp):
            lights_updated += 1

    save_level(c)
    return {
        "materials_applied": applied,
        "materials_skipped": skipped,
        "materials_failed": failed,
        "lights_updated": lights_updated,
    }


def run_floor01_palette(c: MCPClient) -> Dict[str, int]:
    load_level(c, "/Game/Map_Floor01_Ironcatacomb")

    applied = 0
    skipped = 0
    failed = 0

    for actor in get_actors(c, "F1_"):
        name = actor.get("name", "")
        actor_class = actor.get("class", "")
        if actor_class != "StaticMeshActor":
            continue
        material = classify_floor01_material(name)
        if not material:
            skipped += 1
            continue
        if apply_material(c, name, material):
            applied += 1
        else:
            failed += 1

    marker_map = {
        "BP_SafeNode_01": MATS["cyan"],
        "BP_ObjectiveLever_01_A": MATS["bronze"],
        "BP_ObjectiveLever_01_B": MATS["bronze"],
        "BP_BossGate_01": MATS["gold"],
        "BP_SigilSocket_01_1": MATS["cyan"],
        "BP_SigilSocket_01_2": MATS["cyan"],
        "BP_SigilSocket_01_3": MATS["cyan"],
        "BP_BossSpawn_01": MATS["indigo"],
        "BP_AscensionGate_01": MATS["cyan"],
    }
    for name, material in marker_map.items():
        if apply_material(c, name, material):
            applied += 1
        else:
            skipped += 1

    lights_updated = 0
    for actor in get_actors(c, "F1_"):
        name = actor.get("name", "")
        actor_class = actor.get("class", "")
        if "Light" not in actor_class:
            continue
        payload = light_payload_floor01(name, actor_class)
        if not payload:
            continue
        resp = c.send("set_light_properties", payload)
        if ok(resp):
            lights_updated += 1

    save_level(c)
    return {
        "materials_applied": applied,
        "materials_skipped": skipped,
        "materials_failed": failed,
        "lights_updated": lights_updated,
    }


def main() -> int:
    c = MCPClient()
    ping = c.send("ping", {})
    if not ok(ping):
        print(f"ERROR: MCP ping failed: {err_text(ping)}")
        return 2

    hub = run_hub_palette(c)
    floor01 = run_floor01_palette(c)

    print("PALETTE_PASS=done")
    print(f"HUB_MATERIALS_APPLIED={hub['materials_applied']}")
    print(f"HUB_MATERIALS_SKIPPED={hub['materials_skipped']}")
    print(f"HUB_MATERIALS_FAILED={hub['materials_failed']}")
    print(f"HUB_LIGHTS_UPDATED={hub['lights_updated']}")
    print(f"FLOOR01_MATERIALS_APPLIED={floor01['materials_applied']}")
    print(f"FLOOR01_MATERIALS_SKIPPED={floor01['materials_skipped']}")
    print(f"FLOOR01_MATERIALS_FAILED={floor01['materials_failed']}")
    print(f"FLOOR01_LIGHTS_UPDATED={floor01['lights_updated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
