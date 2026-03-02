import unreal

def configure_system_manager():
    bp_path = "/Game/Blueprints/BP_SystemManager"
    bp_asset = unreal.EditorAssetLibrary.load_asset(bp_path)
    
    if not bp_asset:
        print(f"FAILED: Could not find {bp_path}")
        return
        
    # Get the generated class
    bp_class = unreal.EditorBackend.get_blueprint_generated_class(bp_asset)
    if bp_class:
        cdo = unreal.get_default_object(bp_class)
        # Set ProviderMode to Scripted (0)
        cdo.set_editor_property("provider_mode", unreal.SBSystemProviderMode.SCRIPTED)
        print(f"Set BP_SystemManager ProviderMode to SCRIPTED")

    # Also check the actor in the Hub map
    hub_map = "/Game/Map_HubCitadelCity"
    if unreal.EditorLevelLibrary.get_editor_world().get_path_name() != hub_map:
        unreal.EditorLevelLibrary.load_level(hub_map)
        
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if actor.get_class().get_name().startswith("BP_SystemManager"):
            actor.set_editor_property("provider_mode", unreal.SBSystemProviderMode.SCRIPTED)
            print(f"Set Actor {actor.get_name()} ProviderMode to SCRIPTED")

    unreal.EditorLevelLibrary.save_current_level()
    unreal.EditorAssetLibrary.save_asset(bp_path)

if __name__ == "__main__":
    configure_system_manager()
