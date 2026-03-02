import unreal

def check_gamemode():
    gm = unreal.EditorLevelLibrary.get_editor_world().get_game_mode()
    print(f"Current GameMode: {gm.get_name() if gm else 'None'}")
    
    if gm:
        print(f"Default Pawn Class: {gm.default_pawn_class.get_name() if gm.default_pawn_class else 'None'}")
        print(f"HUD Class: {gm.hud_class.get_name() if gm.hud_class else 'None'}")
        print(f"Player Controller Class: {gm.player_controller_class.get_name() if gm.player_controller_class else 'None'}")

    # Also check project settings for default game mode
    # Actually let's just check the BP_SignalBoundGameMode asset
    gm_bp_path = "/Game/Blueprints/BP_SignalBoundGameMode"
    gm_bp = unreal.EditorAssetLibrary.load_asset(gm_bp_path)
    if gm_bp:
        # For Blueprints, we need to check the generated class
        gm_class = unreal.EditorBackend.get_blueprint_generated_class(gm_bp)
        if gm_class:
            cdo = unreal.get_default_object(gm_class)
            print(f"BP_SignalBoundGameMode DefaultPawnClass: {cdo.default_pawn_class.get_name() if cdo.default_pawn_class else 'None'}")

if __name__ == "__main__":
    check_gamemode()
