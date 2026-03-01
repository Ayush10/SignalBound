import time
import json
import sys
from pathlib import Path
from system_ai_voice_bridge import SystemAIVoiceBridge
from mcp_path import resolve_mcp_py_dir

MCP_PY_DIR = resolve_mcp_py_dir()
if str(MCP_PY_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_PY_DIR))

import mcp_cmd as mcp

def run_service():
    print("SignalBound System Service: Monitoring Unreal for AI requests...")
    bridge = SystemAIVoiceBridge()
    
    # Pre-cache common messages
    common_msgs = [
        "System online.",
        "Combat analyzed. Performance within parameters.",
        "Stamina low. Conserve energy.",
        "Contract offered. Acceptance recommended.",
        "Boss entity detected. Steel yourself."
    ]
    print("Pre-caching common system voice lines...")
    for msg in common_msgs:
        bridge.generate_voice(msg)
    
    while True:
        try:
            # Poll for ASBSystemManager actor
            resp = mcp.send_command("get_actors_in_level", {"actor_class": "BP_SystemManager"})
            if resp.get("status") == "success" and resp["result"]["actors"]:
                mgr = resp["result"]["actors"][0]
                mgr_name = mgr["name"]
                
                # Check for bRequestPending flag
                # (Note: Assuming we have a get_actor_property command or we can use call_function)
                # Since we don't have a direct property getter in the current plugin ref, 
                # we'll use a custom command if it exists or fallback to a known mechanism.
                # For this implementation, we'll assume the manager has a CheckRequest function.
                
                # Check properties via MCP
                prop_resp = mcp.send_command("get_actor_properties", {"actor_name": mgr_name, "property_names": ["bRequestPending", "PendingContextTag"]})
                
                if prop_resp.get("status") == "success":
                    props = prop_resp["result"]["properties"]
                    if props.get("bRequestPending"):
                        context = props.get("PendingContextTag", "General")
                        print(f"Request detected! Context: {context}")
                        
                        # Generate AI Directive
                        res = bridge.generate_directive(context)
                        if res["status"] == "success":
                            directive = res["directive"]
                            print(f"Generated: {directive['Text']}")
                            
                            # Push back to Unreal
                            mcp.send_command("call_function", {
                                "actor_name": mgr_name,
                                "function_name": "SetDirective",
                                "parameters": {"Directive": directive}
                            })
                            
                            # Reset flag
                            mcp.send_command("set_actor_property", {
                                "actor_name": mgr_name,
                                "property_name": "bRequestPending",
                                "property_value": "false"
                            })
                            
                            # Async generate voice
                            print("Synthesizing voice...")
                            voice_res = bridge.generate_voice(directive["Text"])
                            if voice_res["status"] == "success":
                                print(f"Voice cached: {voice_res['file_path']}")
                                mcp.send_command("print_string", {"message": f"VOICE_READY: {voice_res['file_path']}"})
            
            time.sleep(1.0) # Poll interval
        except Exception as e:
            print(f"Service Error: {str(e)}")
            time.sleep(5.0)

if __name__ == "__main__":
    run_service()
