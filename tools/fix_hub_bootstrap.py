import unreal
from pathlib import Path


MAP_PATH = "/Game/Map_HubCitadelCity"
GM_BP_CLASS_PATH = "/Game/Blueprints/BP_SignalBoundGameMode.BP_SignalBoundGameMode_C"
POSTPROCESS_BP_PATH = "/Game/Blueprints/BP_SB_PostProcessVolume"
TRIGGER_BP_PATH = "/Game/Blueprints/BP_SB_TriggerVolume"
PLAYERSTART_LABEL = "BP_PlayerStart_Map_HubCitadelCity"
SAFE_PLAYERSTART_LOCATION = unreal.Vector(-18000.0, -7000.0, 250.0)
SAFE_PLAYERSTART_ROTATION = unreal.Rotator(0.0, 20.0, 0.0)


def log(msg: str) -> None:
    unreal.log(f"[HUB_BOOTSTRAP_FIX] {msg}")
    try:
        out = Path(__file__).resolve().parents[1] / "Saved" / "HubFixResult.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def ensure_blueprint(asset_name: str, package_path: str, parent_class) -> None:
    full_asset_path = f"{package_path}/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_asset_path):
        log(f"Asset exists: {full_asset_path}")
        return

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    created = asset_tools.create_asset(asset_name, package_path, unreal.Blueprint, factory)
    if not created:
        raise RuntimeError(f"Failed to create blueprint: {full_asset_path}")
    unreal.EditorAssetLibrary.save_asset(full_asset_path, only_if_is_dirty=False)
    log(f"Created missing blueprint: {full_asset_path}")


def ensure_missing_reference_blueprints() -> None:
    ensure_blueprint("BP_SB_PostProcessVolume", "/Game/Blueprints", unreal.PostProcessVolume)
    ensure_blueprint("BP_SB_TriggerVolume", "/Game/Blueprints", unreal.TriggerBox)


def load_hub_map() -> None:
    loaded = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not loaded:
        raise RuntimeError(f"Failed to load map: {MAP_PATH}")
    log("Loaded hub map.")


def set_world_gamemode_override() -> None:
    gm_class = unreal.load_class(None, GM_BP_CLASS_PATH)
    if not gm_class:
        raise RuntimeError(f"Unable to load class: {GM_BP_CLASS_PATH}")

    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        raise RuntimeError("No editor world.")

    world_settings = world.get_world_settings()
    world_settings.set_editor_property("default_game_mode", gm_class)
    world_settings.modify()
    log("Set hub WorldSettings default_game_mode to BP_SignalBoundGameMode.")


def ensure_player_start() -> None:
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    player_start = None

    for actor in actors:
        if actor.get_class().get_name() == "PlayerStart":
            label = actor.get_actor_label()
            if label == PLAYERSTART_LABEL:
                player_start = actor
                break
            if player_start is None:
                player_start = actor

    if not player_start:
        player_start = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PlayerStart,
            SAFE_PLAYERSTART_LOCATION,
            SAFE_PLAYERSTART_ROTATION,
        )
        log("Spawned new PlayerStart actor.")

    player_start.set_actor_label(PLAYERSTART_LABEL, True)
    player_start.set_actor_location(SAFE_PLAYERSTART_LOCATION, False, True)
    player_start.set_actor_rotation(SAFE_PLAYERSTART_ROTATION, True)
    player_start.modify()
    log(
        f"PlayerStart set to {SAFE_PLAYERSTART_LOCATION.x:.1f}, "
        f"{SAFE_PLAYERSTART_LOCATION.y:.1f}, {SAFE_PLAYERSTART_LOCATION.z:.1f}"
    )


def fix_directional_light_priority() -> None:
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    directional = [a for a in actors if a.get_class().get_name() == "DirectionalLight"]

    if not directional:
        log("No directional lights found in hub map; skipped priority fix.")
        return

    primary = None
    primary_intensity = -1.0
    comps = []
    for actor in directional:
        comp = actor.get_component_by_class(unreal.DirectionalLightComponent)
        if comp:
            comps.append((actor, comp))
            intensity = float(comp.get_editor_property("intensity"))
            if intensity > primary_intensity:
                primary_intensity = intensity
                primary = actor

    if not comps:
        log("Directional lights found but no light components available.")
        return

    for actor, comp in comps:
        priority = 1 if actor == primary else 0
        comp.set_editor_property("forward_shading_priority", priority)
        actor.modify()
    log("Normalized directional light ForwardShadingPriority (primary=1, others=0).")


def save_all() -> None:
    unreal.EditorLevelLibrary.save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log("Saved map and dirty packages.")


def main() -> None:
    ensure_missing_reference_blueprints()
    load_hub_map()
    set_world_gamemode_override()
    ensure_player_start()
    fix_directional_light_priority()
    save_all()
    log("Hub bootstrap fix complete.")


if __name__ == "__main__":
    main()
