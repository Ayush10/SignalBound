import unreal

def fix_gamemode_and_input():
    # Load BP_SignalBoundGameMode
    gm_path = "/Game/Blueprints/BP_SignalBoundGameMode"
    pawn_path = "/Game/Blueprints/BP_PlayerCharacter"
    
    gm_asset = unreal.EditorAssetLibrary.load_asset(gm_path)
    pawn_asset = unreal.EditorAssetLibrary.load_asset(pawn_path)
    
    if not gm_asset:
        print(f"FAILED: Could not find {gm_path}")
        return
        
    if not pawn_asset:
        print(f"FAILED: Could not find {pawn_path}")
        return
        
    # Get the generated classes
    gm_class = unreal.EditorBackend.get_blueprint_generated_class(gm_asset)
    pawn_class = unreal.EditorBackend.get_blueprint_generated_class(pawn_asset)
    
    if gm_class and pawn_class:
        # We need to use Unreal's API to set the default pawn class in the BP
        # This is tricky via Python, but let's try setting it on the CDO
        # Actually, a better way is to set it via the project settings or just modify the BP.
        
        # Let's try to set it via property name
        cdo = unreal.get_default_object(gm_class)
        try:
            cdo.set_editor_property("default_pawn_class", pawn_class)
            print(f"Set default_pawn_class to {pawn_class.get_name()}")
        except Exception as e:
            print(f"Error setting default_pawn_class: {e}")
            
    # Also ensure the level uses this game mode
    hub_map = "/Game/Map_HubCitadelCity"
    if unreal.EditorLevelLibrary.get_editor_world().get_path_name() != hub_map:
        unreal.EditorLevelLibrary.load_level(hub_map)
        
    # Set the World Settings game mode override
    world = unreal.EditorLevelLibrary.get_editor_world()
    settings = world.get_world_settings()
    if settings:
        settings.set_editor_property("default_game_mode", gm_class)
        print(f"Set World Settings GameMode override to {gm_class.get_name()}")

    unreal.EditorLevelLibrary.save_current_level()
    unreal.EditorAssetLibrary.save_asset(gm_path)

if __name__ == "__main__":
    fix_gamemode_and_input()
