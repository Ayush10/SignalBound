import sys
import traceback

import unreal


REPARANT_MAP = [
    ("/Game/Blueprints/BP_PlayerCharacter", "/Script/SignalBound.SBPlayerCharacter"),
    ("/Game/Blueprints/BP_EnemyBase", "/Script/SignalBound.SBEnemyBase"),
    ("/Game/Blueprints/BP_ContractManager", "/Script/SignalBound.SBContractManager"),
    ("/Game/Blueprints/BP_SystemManager", "/Script/SignalBound.SBSystemManager"),
    ("/Game/Blueprints/BP_HUDManager", "/Script/SignalBound.SBHUDManager"),
    ("/Game/Blueprints/BP_SignalBoundGameMode", "/Script/SignalBound.SBSignalBoundGameMode"),
]

MAP_FLOOR01 = "/Game/Map_Floor01_Ironcatacomb"
BP_OBJECTIVE_MANAGER = "/Game/Blueprints/BP_Floor01ObjectiveManager"
BP_OBJECTIVE_MANAGER_CLASS = "/Game/Blueprints/BP_Floor01ObjectiveManager.BP_Floor01ObjectiveManager_C"


def log(msg: str) -> None:
    unreal.log(f"[AUTO_SETUP] {msg}")


def err(msg: str) -> None:
    unreal.log_error(f"[AUTO_SETUP] {msg}")


def load_bp(path: str):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"Failed to load blueprint asset: {path}")
    return asset


def load_class(path: str):
    cls = unreal.load_class(None, path)
    if not cls:
        raise RuntimeError(f"Failed to load class: {path}")
    return cls


def compile_bp(bp) -> None:
    if hasattr(unreal, "KismetEditorUtilities") and hasattr(unreal.KismetEditorUtilities, "compile_blueprint"):
        unreal.KismetEditorUtilities.compile_blueprint(bp)
        return
    if hasattr(unreal, "BlueprintEditorLibrary") and hasattr(unreal.BlueprintEditorLibrary, "compile_blueprint"):
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        return
    log("No exposed compile_blueprint API; continuing")


def reparent_bp(bp, parent_cls) -> None:
    if hasattr(unreal, "BlueprintEditorLibrary") and hasattr(unreal.BlueprintEditorLibrary, "reparent_blueprint"):
        unreal.BlueprintEditorLibrary.reparent_blueprint(bp, parent_cls)
        return
    if hasattr(unreal, "KismetEditorUtilities") and hasattr(unreal.KismetEditorUtilities, "reparent_blueprint"):
        unreal.KismetEditorUtilities.reparent_blueprint(bp, parent_cls)
        return
    if hasattr(unreal, "KismetEditorUtilities") and hasattr(unreal.KismetEditorUtilities, "replace_blueprint_parent_class"):
        unreal.KismetEditorUtilities.replace_blueprint_parent_class(bp, parent_cls)
        return
    raise RuntimeError("No reparent API exposed by Unreal Python in this build")


def save_asset(path: str) -> None:
    ok = unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    if not ok:
        raise RuntimeError(f"Failed to save asset: {path}")


def load_map(path: str) -> None:
    if hasattr(unreal.EditorLevelLibrary, "load_level"):
        ok = unreal.EditorLevelLibrary.load_level(path)
        if not ok:
            raise RuntimeError(f"Failed to load level via EditorLevelLibrary: {path}")
        return
    world = unreal.EditorLoadingAndSavingUtils.load_map(path)
    if not world:
        raise RuntimeError(f"Failed to load level via EditorLoadingAndSavingUtils: {path}")


def actor_label(actor) -> str:
    try:
        return actor.get_actor_label()
    except Exception:
        return ""


def actor_name(actor) -> str:
    try:
        return actor.get_name()
    except Exception:
        return ""


def find_actor_contains(pattern: str):
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        label = actor_label(actor)
        name = actor_name(actor)
        if pattern in label or pattern in name:
            return actor
    return None


def set_obj_property(obj, names, value) -> str:
    last_error = None
    for name in names:
        try:
            obj.set_editor_property(name, value)
            return name
        except Exception as e:
            last_error = e
    raise RuntimeError(f"Could not set property from candidates {names}: {last_error}")


def ensure_floor01_objective_actor():
    manager = find_actor_contains("BP_Floor01ObjectiveManager")
    if manager:
        log(f"Found existing objective manager actor: {actor_name(manager)}")
    else:
        bp_asset = unreal.EditorAssetLibrary.load_asset(BP_OBJECTIVE_MANAGER)
        if bp_asset and hasattr(unreal.EditorLevelLibrary, "spawn_actor_from_object"):
            manager = unreal.EditorLevelLibrary.spawn_actor_from_object(
                bp_asset,
                unreal.Vector(0.0, 0.0, 200.0),
                unreal.Rotator(0.0, 0.0, 0.0),
            )
        if not manager:
            bp_class = load_class(BP_OBJECTIVE_MANAGER_CLASS)
            manager = unreal.EditorLevelLibrary.spawn_actor_from_class(
                bp_class,
                unreal.Vector(0.0, 0.0, 200.0),
                unreal.Rotator(0.0, 0.0, 0.0),
            )
        if not manager:
            raise RuntimeError("Failed to spawn BP_Floor01ObjectiveManager actor")
        manager.set_actor_label("BP_Floor01ObjectiveManager", True)
        log(f"Spawned objective manager actor: {actor_name(manager)}")

    boss_gate = find_actor_contains("BP_BossGate_01")
    if not boss_gate:
        raise RuntimeError("Could not find BP_BossGate_01 actor in Floor01 map")

    asc_trigger = find_actor_contains("BP_LevelTransition_AscensionGate_01")
    if not asc_trigger:
        raise RuntimeError("Could not find BP_LevelTransition_AscensionGate_01 actor in Floor01 map")

    boss_prop = set_obj_property(manager, ["boss_gate_actor", "BossGateActor"], boss_gate)
    asc_prop = set_obj_property(manager, ["ascension_trigger", "AscensionTrigger"], asc_trigger)
    log(f"Assigned properties on objective manager: {boss_prop}, {asc_prop}")


def save_all() -> None:
    if hasattr(unreal.EditorLevelLibrary, "save_current_level"):
        if not unreal.EditorLevelLibrary.save_current_level():
            raise RuntimeError("Failed to save current level")
    else:
        if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
            raise RuntimeError("Failed to save dirty packages")


def main() -> int:
    try:
        log("Starting automated reparent/setup run")

        for bp_path, class_path in REPARANT_MAP:
            bp = load_bp(bp_path)
            parent_cls = load_class(class_path)
            reparent_bp(bp, parent_cls)
            compile_bp(bp)
            save_asset(bp_path)
            log(f"Reparented + compiled + saved: {bp_path} -> {class_path}")

        if not unreal.EditorAssetLibrary.does_asset_exist(BP_OBJECTIVE_MANAGER):
            log("BP_Floor01ObjectiveManager not found, creating from SBFloor01ObjectiveManager")
            if hasattr(unreal, "AssetToolsHelpers"):
                asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                factory = unreal.BlueprintFactory()
                factory.set_editor_property("parent_class", load_class("/Script/SignalBound.SBFloor01ObjectiveManager"))
                asset_tools.create_asset("BP_Floor01ObjectiveManager", "/Game/Blueprints", unreal.Blueprint, factory)
            else:
                raise RuntimeError("Cannot create BP_Floor01ObjectiveManager: AssetToolsHelpers unavailable")

        bp_obj = load_bp(BP_OBJECTIVE_MANAGER)
        compile_bp(bp_obj)
        save_asset(BP_OBJECTIVE_MANAGER)

        load_map(MAP_FLOOR01)
        ensure_floor01_objective_actor()
        save_all()

        log("Automation completed successfully")
        return 0
    except Exception as ex:
        err(f"Automation failed: {ex}")
        err(traceback.format_exc())
        return 1


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
