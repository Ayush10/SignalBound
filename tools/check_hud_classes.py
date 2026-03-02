import unreal

def check_hud_classes():
    hud_path = "/Game/Blueprints/BP_HUDManager"
    hud_asset = unreal.EditorAssetLibrary.load_asset(hud_path)
    if not hud_asset:
        print(f"FAILED: Could not find {hud_path}")
        return
        
    hud_class = unreal.EditorBackend.get_blueprint_generated_class(hud_asset)
    if hud_class:
        cdo = unreal.get_default_object(hud_class)
        print(f"HUD Manager CDO properties:")
        print(f"  PlayerHUDClass: {cdo.player_hud_class.get_name() if cdo.player_hud_class else 'None'}")
        print(f"  SystemNoticeClass: {cdo.system_notice_class.get_name() if cdo.system_notice_class else 'None'}")
        print(f"  SystemMenuClass: {cdo.system_menu_class.get_name() if cdo.system_menu_class else 'None'}")

if __name__ == "__main__":
    check_hud_classes()
