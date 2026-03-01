import json
import sys
import time
from pathlib import Path
from system_ai_voice_bridge import SystemAIVoiceBridge
from mcp_path import resolve_mcp_py_dir

MCP_PY_DIR = resolve_mcp_py_dir()
if str(MCP_PY_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_PY_DIR))

import unreal_mcp_server_advanced as server

def sync_live_directive(context="General"):
    bridge = SystemAIVoiceBridge()
    unreal = server.get_unreal_connection()
    
    print(f"Generating live directive for context: {context}")
    res = bridge.generate_directive(context)
    
    if res["status"] == "success":
        directive = res["directive"]
        print(f"Directive: {directive['Text']}")
        
        # Sync to Unreal
        # We find the SystemManager actor
        mgr_resp = unreal.send_command("get_actors_in_level", {"actor_type": "SBSystemManager"})
        if mgr_resp.get("status") == "success" and mgr_resp["result"]["actors"]:
            mgr_name = mgr_resp["result"]["actors"][0]["name"]
            
            # Call SetDirective via call_function
            unreal.send_command("call_function", {
                "actor_name": mgr_name,
                "function_name": "SetDirective",
                "parameters": {
                    "Directive": {
                        "DirectiveId": directive["DirectiveId"],
                        "Text": directive["Text"],
                        "ContextTag": directive["ContextTag"],
                        "TimestampUtc": directive["TimestampUtc"]
                    }
                }
            })
            
            # Generate voice in background
            print("Generating voice...")
            voice_res = bridge.generate_voice(directive["Text"])
            if voice_res["status"] == "success":
                print(f"Voice ready: {voice_res['file_path']}")
                # Here we could trigger a SoundWave play if we had the plugin command
                # For now, we print it to the log for the HUD to see
                unreal.send_command("print_string", {"message": f"VOICE_PATH={voice_res['file_path']}"})
        else:
            print("Error: Could not find ASBSystemManager in level.")
    else:
        print(f"Error generating directive: {res.get('message')}")

def cache_directives_from_file(file_path):
    """Load a list of directives from a JSON and push to CachedDirectives."""
    if not Path(file_path).exists():
        return
        
    with open(file_path, "r") as f:
        data = json.load(f)
        
    unreal = server.get_unreal_connection()
    mgr_resp = unreal.send_command("get_actors_in_level", {"actor_type": "SBSystemManager"})
    if mgr_resp.get("status") == "success" and mgr_resp["result"]["actors"]:
        mgr_name = mgr_resp["result"]["actors"][0]["name"]
        for d in data.get("directives", []):
            unreal.send_command("call_function", {
                "actor_name": mgr_name,
                "function_name": "AddCachedDirective",
                "parameters": {"Directive": d}
            })
        print(f"Cached {len(data.get('directives', []))} directives.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["live", "cache"], default="live")
    parser.add_argument("--context", default="General")
    parser.add_argument("--file", default="Saved/SystemCache/directives_cache.json")
    args = parser.parse_args()
    
    if args.mode == "live":
        sync_live_directive(args.context)
    else:
        cache_directives_from_file(args.file)
