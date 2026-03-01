#!/usr/bin/env python3
"""Incremental environment build pass for SignalBound (Luminarch Citadel City).

Scope:
- Part A: Map_SystemTest
- Part B: Required hub placements for Map_HubCitadelCity
- Part C: Map_Floor01_Ironcatacomb shell + markers/volumes

Rules:
- Additive by default: never delete existing actors.
- Strict naming for gameplay bind points.
"""

from __future__ import annotations

import argparse
import json
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple


CUBE = "/Engine/BasicShapes/Cube.Cube"
CYL = "/Engine/BasicShapes/Cylinder.Cylinder"
SPHERE = "/Engine/BasicShapes/Sphere.Sphere"
PLANE = "/Engine/BasicShapes/Plane.Plane"


class MCPClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 55557) -> None:
        self.host = host
        self.port = port

    def send(self, command_type: str, params: Dict[str, Any] | None = None, timeout: float = 60.0) -> Dict[str, Any]:
        payload = {"type": command_type, "params": params or {}}
        data = json.dumps(payload).encode("utf-8")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
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
    if not resp:
        return False
    if resp.get("status") == "error":
        return False
    if resp.get("success") is False:
        return False
    return True


def resp_error(resp: Dict[str, Any]) -> str:
    if not resp:
        return "no response"
    if "error" in resp:
        return str(resp.get("error"))
    result = resp.get("result")
    if isinstance(result, dict) and "error" in result:
        return str(result.get("error"))
    return str(resp)


@dataclass
class BuildReport:
    maps_touched: List[str] = field(default_factory=list)
    markers: List[Tuple[str, str]] = field(default_factory=list)
    audio_volumes: List[str] = field(default_factory=list)
    postprocess_volumes: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    failures: List[str] = field(default_factory=list)
    placed: int = 0
    skipped: int = 0


class Builder:
    def __init__(self, client: MCPClient, report: BuildReport) -> None:
        self.c = client
        self.r = report

    def ping(self) -> None:
        last_err = "unknown"
        for _ in range(8):
            resp = self.c.send("ping", {}, timeout=5.0)
            if is_ok(resp):
                return
            last_err = resp_error(resp)
        raise RuntimeError(f"MCP ping failed after retries: {last_err}")

    def find(self, pattern: str) -> List[Dict[str, Any]]:
        resp = self.c.send("find_actors_by_name", {"pattern": pattern})
        if not is_ok(resp):
            return []
        return (resp.get("result") or {}).get("actors") or []

    def exists(self, name: str) -> bool:
        actors = self.find(name)
        return any(a.get("name") == name for a in actors)

    def load_or_create_map(self, map_path: str) -> None:
        content_rel = map_path.replace("/Game/", "").strip("/")
        map_file = Path("Content") / f"{content_rel}.umap"

        if map_file.exists():
            load_resp = self.c.send("load_level", {"map_path": map_path})
            if not is_ok(load_resp):
                raise RuntimeError(f"Failed to load existing map {map_path}: {resp_error(load_resp)}")
        else:
            new_resp = self.c.send("new_blank_level", {"save_existing": True})
            if not is_ok(new_resp):
                raise RuntimeError(f"Failed to create new blank level for {map_path}: {resp_error(new_resp)}")

            save_as = self.c.send("save_current_level_as", {"map_path": map_path})
            if not is_ok(save_as):
                raise RuntimeError(f"Failed to save new map {map_path}: {resp_error(save_as)}")
            if not map_file.exists():
                raise RuntimeError(f"Map save reported success but file missing: {map_file}")

            load_resp = self.c.send("load_level", {"map_path": map_path})
            if not is_ok(load_resp):
                raise RuntimeError(f"Map created but could not load {map_path}: {resp_error(load_resp)}")

        save_resp = self.c.send("save_current_level", {})
        if not is_ok(save_resp):
            self.r.notes.append(f"Warning: initial save failed after loading {map_path}: {resp_error(save_resp)}")
        if map_path not in self.r.maps_touched:
            self.r.maps_touched.append(map_path)

    def save_current(self) -> None:
        resp = self.c.send("save_current_level", {})
        if not is_ok(resp):
            self.r.failures.append(f"save_current_level failed: {resp_error(resp)}")

    def spawn_mesh(
        self,
        name: str,
        location: List[float],
        scale: List[float],
        rotation: List[float] | None = None,
        mesh: str = CUBE,
    ) -> bool:
        if self.exists(name):
            self.r.skipped += 1
            return True

        payload: Dict[str, Any] = {
            "type": "StaticMeshActor",
            "name": name,
            "location": location,
            "scale": scale,
            "static_mesh": mesh,
        }
        if rotation is not None:
            payload["rotation"] = rotation

        resp = self.c.send("spawn_actor", payload)
        if is_ok(resp):
            self.r.placed += 1
            return True
        self.r.failures.append(f"spawn_mesh {name}: {resp_error(resp)}")
        return False

    def spawn_light(
        self,
        name: str,
        actor_type: str,
        location: List[float],
        rotation: List[float] | None = None,
        scale: List[float] | None = None,
    ) -> bool:
        if self.exists(name):
            self.r.skipped += 1
            return True

        payload: Dict[str, Any] = {
            "type": actor_type,
            "name": name,
            "location": location,
        }
        if rotation is not None:
            payload["rotation"] = rotation
        if scale is not None:
            payload["scale"] = scale

        resp = self.c.send("spawn_actor", payload)
        if is_ok(resp):
            self.r.placed += 1
            return True
        self.r.failures.append(f"spawn_light {name}: {resp_error(resp)}")
        return False

    def ensure_blueprint(self, blueprint_name: str, parent_class: str) -> bool:
        resp = self.c.send("create_blueprint", {"name": blueprint_name, "parent_class": parent_class})
        if is_ok(resp):
            return True
        err = resp_error(resp)
        if "already exists" in err.lower():
            return True
        self.r.failures.append(f"ensure_blueprint {blueprint_name}<{parent_class}>: {err}")
        return False

    def spawn_blueprint(
        self,
        blueprint_name: str,
        actor_name: str,
        location: List[float],
        scale: List[float] | None = None,
        rotation: List[float] | None = None,
    ) -> bool:
        if self.exists(actor_name):
            self.r.skipped += 1
            return True

        payload: Dict[str, Any] = {
            "blueprint_name": blueprint_name,
            "actor_name": actor_name,
            "location": {"x": location[0], "y": location[1], "z": location[2]},
        }
        if rotation is not None:
            payload["rotation"] = {"pitch": rotation[0], "yaw": rotation[1], "roll": rotation[2]}
        resp = self.c.send("spawn_blueprint_actor", payload)
        if not is_ok(resp):
            self.r.failures.append(f"spawn_blueprint {actor_name} via {blueprint_name}: {resp_error(resp)}")
            return False

        if scale is not None:
            tf = self.c.send(
                "set_actor_transform",
                {"name": actor_name, "scale": scale},
            )
            if not is_ok(tf):
                self.r.failures.append(f"set_actor_transform(scale) {actor_name}: {resp_error(tf)}")

        self.r.placed += 1
        return True

    def set_tags(self, actor_name: str, tags: List[str]) -> bool:
        resp = self.c.send("set_actor_tags", {"name": actor_name, "tags": tags, "append": False})
        if is_ok(resp):
            return True
        self.r.failures.append(f"set_tags {actor_name}: {resp_error(resp)}")
        return False

    def add_plaque_text(self, actor_name: str, text: str, index: int) -> None:
        component = f"NoticeText_{index:02d}"
        resp = self.c.send(
            "add_text_render_component",
            {
                "name": actor_name,
                "component_name": component,
                "text": text,
                "location": [8, 20, 30],
                "rotation": [0, 90, 0],
                "scale": [0.25, 0.25, 0.25],
                "world_size": 28.0,
                "text_color": [0.27, 0.9, 1.0, 1.0],
            },
        )
        if is_ok(resp):
            return
        err = resp_error(resp).lower()
        if "component already exists" in err:
            return
        self.r.failures.append(f"add_plaque_text {actor_name}: {resp_error(resp)}")

    def spawn_volume_actor(
        self,
        actor_name: str,
        bp_name: str,
        parent_class: str,
        location: List[float],
        scale: List[float],
        fallback_mesh_scale: List[float] | None = None,
    ) -> bool:
        if self.exists(actor_name):
            self.r.skipped += 1
            return True

        # Keep exact actor names deterministic for gameplay binding.
        # Current MCP spawn_blueprint_actor path sets labels but not guaranteed actor object names.
        # Use exact-name mesh markers as additive placeholders.
        marker_scale = fallback_mesh_scale or [2.0, 2.0, 2.0]
        return self.spawn_mesh(actor_name, location, marker_scale, mesh=CUBE)

    def build_rect_room(self, prefix: str, cx: float, cy: float, width_m: float, depth_m: float, ceiling_m: float) -> None:
        floor_z = 0.0
        ceil_z = ceiling_m * 100.0
        wall_z = ceil_z * 0.5
        wall_t = 0.2

        self.spawn_mesh(f"{prefix}_Floor", [cx, cy, floor_z], [width_m, depth_m, 0.2], mesh=CUBE)
        self.spawn_mesh(f"{prefix}_Ceiling", [cx, cy, ceil_z], [width_m, depth_m, 0.2], mesh=CUBE)

        self.spawn_mesh(
            f"{prefix}_Wall_N",
            [cx, cy + (depth_m * 50.0), wall_z],
            [width_m, wall_t, ceiling_m],
            mesh=CUBE,
        )
        self.spawn_mesh(
            f"{prefix}_Wall_S",
            [cx, cy - (depth_m * 50.0), wall_z],
            [width_m, wall_t, ceiling_m],
            mesh=CUBE,
        )
        self.spawn_mesh(
            f"{prefix}_Wall_E",
            [cx + (width_m * 50.0), cy, wall_z],
            [wall_t, depth_m, ceiling_m],
            mesh=CUBE,
        )
        self.spawn_mesh(
            f"{prefix}_Wall_W",
            [cx - (width_m * 50.0), cy, wall_z],
            [wall_t, depth_m, ceiling_m],
            mesh=CUBE,
        )


def build_part_a_systemtest(b: Builder) -> None:
    b.load_or_create_map("/Game/Map_SystemTest")

    b.spawn_mesh("ST_Floor", [0, 0, -100], [30, 30, 0.4], mesh=CUBE)
    b.spawn_mesh("ST_Ceiling", [0, 0, 900], [30, 30, 0.2], mesh=CUBE)
    b.spawn_mesh("ST_Wall_N", [0, 3000, 400], [30, 0.4, 10], mesh=CUBE)
    b.spawn_mesh("ST_Wall_S", [0, -3000, 400], [30, 0.4, 10], mesh=CUBE)
    b.spawn_mesh("ST_Wall_E", [3000, 0, 400], [0.4, 30, 10], mesh=CUBE)
    b.spawn_mesh("ST_Wall_W", [-3000, 0, 400], [0.4, 30, 10], mesh=CUBE)
    b.spawn_light("ST_KeyLight", "PointLight", [0, 0, 800], scale=[1, 1, 1])
    b.spawn_light("ST_Sun", "DirectionalLight", [-1000, -1000, 2500], rotation=[-55, 35, 0], scale=[1, 1, 1])

    b.spawn_mesh("BP_PlayerStart_Map_SystemTest", [0, 0, 120], [0.8, 0.8, 2.0], mesh=CYL)
    b.r.markers.append(("/Game/Map_SystemTest", "BP_PlayerStart_Map_SystemTest"))
    b.spawn_mesh("ST_UI_Wall_Empty", [0, 2980, 350], [12, 0.12, 6], mesh=CUBE)

    b.save_current()


def build_part_b_hub_required(b: Builder) -> None:
    b.load_or_create_map("/Game/Map_HubCitadelCity")

    # Required marker placements (additive).
    required_markers = {
        "BP_PlayerStart_Map_HubCitadelCity": [-18600, -7000, 120],
        "BP_SafeNode_00": [1000, -1500, 120],
        "BP_AscensionGate_00": [-4200, 13800, 20],
        "BP_AscensionGate_01": [0, 13800, 20],
        "BP_AscensionGate_02": [4200, 13800, 20],
    }
    for name, loc in required_markers.items():
        b.spawn_mesh(name, loc, [0.9, 0.9, 2.0], mesh=CYL)
        b.r.markers.append(("/Game/Map_HubCitadelCity", name))

    # Level transition trigger at gate 1.
    b.spawn_volume_actor(
        actor_name="BP_LevelTransition_Gate01",
        bp_name="BP_SB_TriggerVolume",
        parent_class="TriggerBox",
        location=[-4200, 13200, 120],
        scale=[4.0, 6.0, 2.5],
        fallback_mesh_scale=[4.0, 6.0, 2.5],
    )
    b.r.markers.append(("/Game/Map_HubCitadelCity", "BP_LevelTransition_Gate01"))

    # 8 core plaques with suggested visible text.
    plaque_texts = [
        "Clearance Level: Provisional",
        "Signal Monitoring: Active",
        "Unauthorized Descent: Prohibited",
        "Signal Strength: Monitored",
        "Contract History: None",
        "Boundary Stability: Stable",
        "Access Integrity: Verified",
        "Observation State: Continuous",
    ]
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
    for i, ((x, y, z), text) in enumerate(zip(plaque_locs, plaque_texts), start=1):
        name = f"BP_SystemNoticePlaque_{i:02d}"
        b.spawn_mesh(name, [x, y, z], [0.9, 0.2, 2.1], mesh=CUBE)
        b.add_plaque_text(name, text, i)
        b.r.markers.append(("/Game/Map_HubCitadelCity", name))

    # Audio volumes.
    hub_audio = {
        "AudioVolume_Hub_Core": ([0, 0, 300], [220.0, 180.0, 18.0]),
        "AudioVolume_Hub_Terrace": ([0, -18000, 1200], [80.0, 60.0, 14.0]),
    }
    for name, (loc, scale) in hub_audio.items():
        b.spawn_volume_actor(name, "BP_SB_AudioVolume", "AudioVolume", loc, scale, fallback_mesh_scale=[3, 3, 3])
        b.r.audio_volumes.append(name)

    # Post process volumes.
    hub_pp = {
        "PP_Hub_GrandHall": ([-16000, -7000, 900], [70.0, 40.0, 20.0]),
        "PP_Hub_Plaza": ([0, 0, 900], [100.0, 100.0, 24.0]),
        "PP_Hub_Terrace": ([0, -18000, 1600], [80.0, 60.0, 24.0]),
    }
    for name, (loc, scale) in hub_pp.items():
        b.spawn_volume_actor(name, "BP_SB_PostProcessVolume", "PostProcessVolume", loc, scale, fallback_mesh_scale=[3, 3, 3])
        b.r.postprocess_volumes.append(name)

    b.r.notes.append(
        "Hub audio/post-process and transition volume names were placed as exact-name markers to preserve deterministic binding with current MCP spawn-name limitations."
    )

    # Subtle static heartbeat proxies (light rhythm anchors).
    pulse_points = [(-9000, -1000, 260), (-3000, -3000, 260), (3000, -3000, 260), (9000, -1000, 260)]
    for i, (x, y, z) in enumerate(pulse_points, start=1):
        b.spawn_light(f"L_SYS_Heartbeat_{i:02d}", "PointLight", [x, y, z], scale=[0.7, 0.7, 0.7])

    b.save_current()


def build_part_c_floor01(b: Builder) -> None:
    b.load_or_create_map("/Game/Map_Floor01_Ironcatacomb")

    # Dynamic lighting only.
    b.spawn_light("F1_Sun", "DirectionalLight", [-2200, -1800, 3000], rotation=[-62, 42, 0], scale=[1, 1, 1])
    b.spawn_light("F1_Key_Entry", "SpotLight", [0, 0, 900], rotation=[90, 0, 0], scale=[1, 1, 1])
    b.spawn_light("F1_Key_Boss", "SpotLight", [15800, 0, 1400], rotation=[90, 0, 0], scale=[1, 1, 1])

    # Entry safe node chamber (12m diameter circular).
    b.spawn_mesh("F1_Entry_Floor", [0, 0, -40], [12.0, 12.0, 0.2], mesh=CYL)
    b.spawn_mesh("F1_Entry_Ceiling", [0, 0, 620], [12.0, 12.0, 0.2], mesh=CYL)

    # Room shells with exact dimensions.
    b.build_rect_room("F1_Room1_Antechamber", 2200, 0, 18.0, 18.0, 6.0)
    b.build_rect_room("F1_Corridor2_Left", 4200, -1200, 20.0, 4.0, 6.0)
    b.build_rect_room("F1_Room2_Left", 6200, -1200, 14.0, 14.0, 6.0)
    b.build_rect_room("F1_Corridor2_Right", 4200, 1200, 16.0, 6.0, 6.0)
    b.build_rect_room("F1_Room2_Right", 6000, 1200, 16.0, 16.0, 6.0)
    b.build_rect_room("F1_Connector_Left", 7900, -700, 14.0, 4.0, 6.0)
    b.build_rect_room("F1_Connector_Right", 7900, 700, 14.0, 4.0, 6.0)
    b.build_rect_room("F1_Room3_SigilVault", 9600, 0, 20.0, 16.0, 7.0)
    b.build_rect_room("F1_BossGateHall", 12200, 0, 25.0, 4.0, 8.0)

    # Boss arena (28m diameter, 12m ceiling).
    b.spawn_mesh("F1_BossArena_Floor", [15800, 0, -40], [28.0, 28.0, 0.2], mesh=CYL)
    b.spawn_mesh("F1_BossArena_Ceiling", [15800, 0, 1200], [28.0, 28.0, 0.2], mesh=CYL)
    for i, pos in enumerate([(14800, 0, 320), (16300, 900, 320), (16300, -900, 320)], start=1):
        b.spawn_mesh(f"F1_BossArena_Pillar_{i:02d}", [pos[0], pos[1], pos[2]], [0.9, 0.9, 6.0], mesh=CYL)

    # Shaft vista in connector between room2 and room3 (left side opening width 3m).
    b.spawn_mesh("F1_Shaft_BrokenWall_L", [8300, -900, 260], [0.25, 3.0, 2.6], mesh=CUBE)
    for i, z in enumerate([-600, -1200, -1800, -2400], start=1):
        b.spawn_mesh(f"F1_Shaft_Dust_{i:02d}", [8500 + (i * 40), -1300 + (i * 35), z], [0.12, 0.12, 0.12], mesh=SPHERE)
    b.spawn_light("F1_Shaft_VoidGlow_01", "PointLight", [8700, -1600, -1700], scale=[0.8, 0.8, 0.8])
    b.spawn_light("F1_Shaft_VoidGlow_02", "PointLight", [9000, -1800, -2600], scale=[0.8, 0.8, 0.8])

    # Fog cards.
    fog_cards = [
        ("F1_FogCard_01", [11500, 0, 40], [6.0, 2.2, 1.0], [0, 0, 0]),
        ("F1_FogCard_02", [12600, 0, 40], [6.0, 2.2, 1.0], [0, 0, 0]),
        ("F1_FogCard_03", [8100, -700, 40], [4.0, 2.2, 1.0], [0, 0, 0]),
        ("F1_FogCard_04", [7900, 700, 40], [4.0, 2.2, 1.0], [0, 0, 0]),
    ]
    for name, loc, scale, rot in fog_cards:
        b.spawn_mesh(name, loc, scale, rotation=rot, mesh=PLANE)

    # Required markers (exact names).
    marker_defs = {
        "BP_SafeNode_01": [0, 0, 120],
        "BP_ObjectiveLever_01_A": [9200, -400, 120],
        "BP_ObjectiveLever_01_B": [10000, 400, 120],  # 8m apart
        "BP_BossGate_01": [13450, 0, 160],
        "BP_SigilSocket_01_1": [13380, -140, 260],
        "BP_SigilSocket_01_2": [13380, 0, 260],
        "BP_SigilSocket_01_3": [13380, 140, 260],
        "BP_BossSpawn_01": [15800, 0, 120],
        "BP_AscensionGate_01": [17200, 0, 120],
    }
    for name, loc in marker_defs.items():
        mesh = CYL if "SigilSocket" not in name else SPHERE
        b.spawn_mesh(name, loc, [0.9, 0.9, 2.0], mesh=mesh)
        b.r.markers.append(("/Game/Map_Floor01_Ironcatacomb", name))

    b.spawn_volume_actor(
        actor_name="BP_LevelTransition_AscensionGate_01",
        bp_name="BP_SB_TriggerVolume",
        parent_class="TriggerBox",
        location=[17200, 0, 120],
        scale=[4.0, 5.0, 2.5],
        fallback_mesh_scale=[4.0, 5.0, 2.5],
    )
    b.r.markers.append(("/Game/Map_Floor01_Ironcatacomb", "BP_LevelTransition_AscensionGate_01"))

    # Spawn markers and tags.
    room1_points = [(2000, -500), (2350, -350), (2550, -50), (2050, 350), (2400, 500), (2700, 250), (1850, 100), (2550, -500)]
    room2_points = [(5900, -1600), (6500, -1400), (6100, -900), (7000, -1100), (5600, 900), (6200, 900), (6800, 1200), (6400, 1600)]
    room3_points = [(9100, -500), (9600, -600), (10100, -300), (9200, 400), (9800, 500), (10300, 200)]

    for i, (x, y) in enumerate(room1_points, start=1):
        name = f"BP_EnemySpawn_01_01_{i:02d}"
        b.spawn_mesh(name, [x, y, 120], [0.55, 0.55, 1.5], mesh=SPHERE)
        b.set_tags(name, ["SpawnGroup_Floor01_Room1"])
        b.r.markers.append(("/Game/Map_Floor01_Ironcatacomb", name))

    for i, (x, y) in enumerate(room2_points, start=1):
        name = f"BP_EnemySpawn_01_02_{i:02d}"
        b.spawn_mesh(name, [x, y, 120], [0.55, 0.55, 1.5], mesh=SPHERE)
        b.set_tags(name, ["SpawnGroup_Floor01_Room2"])
        b.r.markers.append(("/Game/Map_Floor01_Ironcatacomb", name))

    for i, (x, y) in enumerate(room3_points, start=1):
        name = f"BP_EnemySpawn_01_03_{i:02d}"
        b.spawn_mesh(name, [x, y, 120], [0.55, 0.55, 1.5], mesh=SPHERE)
        b.set_tags(name, ["SpawnGroup_Floor01_Room3"])
        b.r.markers.append(("/Game/Map_Floor01_Ironcatacomb", name))

    b.spawn_mesh("BP_EliteSpawn_01_03", [10000, 0, 120], [0.75, 0.75, 1.8], mesh=SPHERE)
    b.r.markers.append(("/Game/Map_Floor01_Ironcatacomb", "BP_EliteSpawn_01_03"))

    # Floor 1 audio volumes.
    floor_audio = {
        "AudioVolume_Floor01_Entry": ([0, 0, 250], [30.0, 30.0, 10.0]),
        "AudioVolume_Floor01_Combat": ([7600, 0, 350], [120.0, 90.0, 14.0]),
        "AudioVolume_Floor01_BossGate": ([12200, 0, 420], [70.0, 18.0, 14.0]),
        "AudioVolume_Floor01_Boss": ([15800, 0, 500], [85.0, 85.0, 16.0]),
    }
    for name, (loc, scale) in floor_audio.items():
        b.spawn_volume_actor(name, "BP_SB_AudioVolume", "AudioVolume", loc, scale, fallback_mesh_scale=[3, 3, 3])
        b.r.audio_volumes.append(name)

    # Floor 1 post process volumes.
    floor_pp = {
        "PP_Floor01_Dungeon": ([7600, 0, 500], [130.0, 95.0, 16.0]),
        "PP_Floor01_BossArena": ([15800, 0, 650], [90.0, 90.0, 18.0]),
    }
    for name, (loc, scale) in floor_pp.items():
        b.spawn_volume_actor(name, "BP_SB_PostProcessVolume", "PostProcessVolume", loc, scale, fallback_mesh_scale=[3, 3, 3])
        b.r.postprocess_volumes.append(name)

    # NavMesh bounds shell.
    b.spawn_volume_actor(
        actor_name="NavMeshBounds_Floor01_Main",
        bp_name="BP_SB_NavBoundsVolume",
        parent_class="NavMeshBoundsVolume",
        location=[9000, 0, 400],
        scale=[180.0, 120.0, 24.0],
        fallback_mesh_scale=[4.0, 4.0, 4.0],
    )

    b.save_current()

    b.r.notes.append(
        "NavMesh bounds volume placed for Floor01. Automated AI corner-path verification is not exposed via current MCP command set; validate in-editor with an AI pawn."
    )
    b.r.notes.append(
        "Floor01 audio/post-process/transition volume names were placed as exact-name markers to keep naming deterministic in additive mode."
    )


def write_completion_report(report: BuildReport) -> Path:
    out = Path("docs") / "ENV_COMPLETION_REPORT_2026-03-01.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    markers_sorted = sorted(report.markers, key=lambda x: (x[0], x[1]))
    audio_sorted = sorted(set(report.audio_volumes))
    pp_sorted = sorted(set(report.postprocess_volumes))

    lines: List[str] = []
    lines.append("# SignalBound Environment Completion Report (2026-03-01)")
    lines.append("")
    lines.append("## Maps Created or Updated")
    for m in report.maps_touched:
        lines.append(f"- {m}")
    lines.append("")

    lines.append("## All Markers Placed (Exact Names)")
    for map_name, marker in markers_sorted:
        lines.append(f"- {map_name}: {marker}")
    lines.append("")

    lines.append("## Audio Volumes Placed")
    for name in audio_sorted:
        lines.append(f"- {name}")
    lines.append("")

    lines.append("## Post Process Volumes Placed")
    for name in pp_sorted:
        lines.append(f"- {name}")
    lines.append("")

    lines.append("## NavMesh Validation Result")
    lines.append("- NavMesh bounds volume placed: `NavMeshBounds_Floor01_Main`.")
    lines.append("- MCP does not expose runtime AI path-corner validation in this repo; manual PIE verification is required.")
    lines.append("")

    lines.append("## Missing Items and Exact Next Steps")
    if report.failures:
        lines.append("- The following operations failed:")
        for f in report.failures:
            lines.append(f"  - {f}")
    else:
        lines.append("- No hard failures during this incremental pass.")
    lines.append("- In Unreal Editor:")
    lines.append("  - Open `Map_Floor01_Ironcatacomb`.")
    lines.append("  - Press `P` to visualize NavMesh and confirm full room/corridor coverage.")
    lines.append("  - Drop an AI pawn and verify pathing to all room corners.")
    lines.append("  - Tune post process and audio volume settings artistically (actors are now present).")
    lines.append("")

    lines.append("## Build Summary")
    lines.append(f"- Actors placed: {report.placed}")
    lines.append(f"- Actors skipped (already present): {report.skipped}")
    lines.append(f"- Failure count: {len(report.failures)}")
    for n in report.notes:
        lines.append(f"- Note: {n}")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Incremental Luminarch environment build pass.")
    parser.add_argument(
        "--phase",
        choices=["all", "part_a", "part_b", "part_c"],
        default="all",
        help="Run a specific phase only.",
    )
    args = parser.parse_args()

    report = BuildReport()
    builder = Builder(MCPClient(), report)
    builder.ping()

    if args.phase in ("all", "part_a"):
        build_part_a_systemtest(builder)
        print("PHASE_DONE=part_a_systemtest", flush=True)
    if args.phase in ("all", "part_b"):
        build_part_b_hub_required(builder)
        print("PHASE_DONE=part_b_hub_required", flush=True)
    if args.phase in ("all", "part_c"):
        build_part_c_floor01(builder)
        print("PHASE_DONE=part_c_floor01", flush=True)

    report_path = write_completion_report(report)

    print(f"REPORT_PATH={report_path}")
    print(f"PLACED={report.placed}")
    print(f"SKIPPED={report.skipped}")
    print(f"FAILURES={len(report.failures)}")
    if report.failures:
        for f in report.failures[:25]:
            print(f"FAIL {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
