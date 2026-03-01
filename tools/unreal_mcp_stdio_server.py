#!/usr/bin/env python3
"""MCP stdio server that bridges Claude Code to the Unreal Editor TCP plugin on port 55557."""

import json
import socket
from mcp.server.fastmcp import FastMCP

MCP_HOST = "127.0.0.1"
MCP_PORT = 55557
TIMEOUT = 30

mcp = FastMCP("UnrealMCP")


def send_command(cmd_type: str, params: dict | None = None, timeout: int = TIMEOUT) -> dict:
    """Send a raw TCP command to the Unreal MCP plugin and return the response."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((MCP_HOST, MCP_PORT))
        command = {"type": cmd_type, "params": params or {}}
        sock.sendall(json.dumps(command).encode("utf-8"))
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                return json.loads(b"".join(chunks).decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        return {"status": "error", "error": "No response from Unreal"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    finally:
        sock.close()


# ── Connectivity ──────────────────────────────────────────────────────

@mcp.tool()
def ping() -> str:
    """Ping the Unreal Editor MCP plugin to check connectivity."""
    return json.dumps(send_command("ping"))


# ── Actor / Level Management ─────────────────────────────────────────

@mcp.tool()
def get_actors_in_level(actor_type: str = "", name_contains: str = "", max_results: int = 100) -> str:
    """List actors in the current level. Optional filters: actor_type, name_contains, max_results."""
    params = {}
    if actor_type:
        params["actor_type"] = actor_type
    if name_contains:
        params["name_contains"] = name_contains
    if max_results:
        params["max_results"] = max_results
    return json.dumps(send_command("get_actors_in_level", params))


@mcp.tool()
def find_actors_by_name(pattern: str) -> str:
    """Find actors whose name matches the given pattern."""
    return json.dumps(send_command("find_actors_by_name", {"pattern": pattern}))


@mcp.tool()
def delete_actor(actor_name: str) -> str:
    """Delete an actor from the level by name."""
    return json.dumps(send_command("delete_actor", {"actor_name": actor_name}))


@mcp.tool()
def set_actor_transform(actor_name: str, location: dict = None, rotation: dict = None, scale: dict = None) -> str:
    """Set an actor's transform (location, rotation, scale). Each is {x,y,z}."""
    params = {"actor_name": actor_name}
    if location:
        params["location"] = location
    if rotation:
        params["rotation"] = rotation
    if scale:
        params["scale"] = scale
    return json.dumps(send_command("set_actor_transform", params))


@mcp.tool()
def spawn_blueprint_actor(blueprint_name: str, actor_name: str, location: dict = None) -> str:
    """Spawn a blueprint actor in the level. location is {x,y,z}."""
    params = {"blueprint_name": blueprint_name, "actor_name": actor_name}
    if location:
        params["location"] = location
    return json.dumps(send_command("spawn_blueprint_actor", params))


@mcp.tool()
def set_actor_tags(actor_name: str, tags: list[str], append: bool = False) -> str:
    """Set or append tags on an actor."""
    return json.dumps(send_command("set_actor_tags", {"actor_name": actor_name, "tags": tags, "append": append}))


@mcp.tool()
def set_actor_label(actor_name: str, label: str) -> str:
    """Set the editor display label on an actor."""
    return json.dumps(send_command("set_actor_label", {"actor_name": actor_name, "label": label}))


# ── Blueprint Creation ────────────────────────────────────────────────

@mcp.tool()
def create_blueprint(name: str, parent_class: str = "Actor") -> str:
    """Create a new Blueprint asset. parent_class examples: Actor, Character, GameModeBase."""
    return json.dumps(send_command("create_blueprint", {"name": name, "parent_class": parent_class}))


@mcp.tool()
def add_component_to_blueprint(blueprint_name: str, component_name: str, component_type: str, parent_component: str = "") -> str:
    """Add a component to a blueprint. component_type must be full path like /Script/Engine.StaticMeshComponent."""
    params = {"blueprint_name": blueprint_name, "component_name": component_name, "component_type": component_type}
    if parent_component:
        params["parent_component"] = parent_component
    return json.dumps(send_command("add_component_to_blueprint", params))


@mcp.tool()
def set_static_mesh_properties(blueprint_name: str, component_name: str, static_mesh: str = "", material: str = "") -> str:
    """Set static mesh and/or material on a blueprint's mesh component."""
    params = {"blueprint_name": blueprint_name, "component_name": component_name}
    if static_mesh:
        params["static_mesh"] = static_mesh
    if material:
        params["material"] = material
    return json.dumps(send_command("set_static_mesh_properties", params))


@mcp.tool()
def compile_blueprint(blueprint_name: str) -> str:
    """Compile a blueprint."""
    return json.dumps(send_command("compile_blueprint", {"blueprint_name": blueprint_name}))


# ── Blueprint Graph ───────────────────────────────────────────────────

@mcp.tool()
def add_node(blueprint_name: str, node_type: str, node_params: dict = None, function_name: str = "") -> str:
    """Add a node to a blueprint's event graph or function graph. node_type: Branch, VariableGet, VariableSet, CallFunction, Print, etc."""
    params = {"blueprint_name": blueprint_name, "node_type": node_type}
    if node_params:
        params["node_params"] = node_params
    if function_name:
        params["function_name"] = function_name
    return json.dumps(send_command("add_node", params))


@mcp.tool()
def connect_nodes(blueprint_name: str, source_node_id: str, source_pin_name: str, target_node_id: str, target_pin_name: str, function_name: str = "") -> str:
    """Connect two nodes' pins in a blueprint graph."""
    params = {
        "blueprint_name": blueprint_name,
        "source_node_id": source_node_id,
        "source_pin_name": source_pin_name,
        "target_node_id": target_node_id,
        "target_pin_name": target_pin_name,
    }
    if function_name:
        params["function_name"] = function_name
    return json.dumps(send_command("connect_nodes", params))


@mcp.tool()
def delete_node(blueprint_name: str, node_id: str, function_name: str = "") -> str:
    """Delete a node from a blueprint graph."""
    params = {"blueprint_name": blueprint_name, "node_id": node_id}
    if function_name:
        params["function_name"] = function_name
    return json.dumps(send_command("delete_node", params))


@mcp.tool()
def create_variable(blueprint_name: str, variable_name: str, variable_type: str, default_value: str = "", category: str = "") -> str:
    """Create a variable on a blueprint. variable_type: Boolean, Integer, Float, String, Vector, Name, etc."""
    params = {"blueprint_name": blueprint_name, "variable_name": variable_name, "variable_type": variable_type}
    if default_value:
        params["default_value"] = default_value
    if category:
        params["category"] = category
    return json.dumps(send_command("create_variable", params))


@mcp.tool()
def set_blueprint_variable_properties(blueprint_name: str, variable_name: str, default_value: str = "", category: str = "") -> str:
    """Set properties on an existing blueprint variable (default value, category, etc.)."""
    params = {"blueprint_name": blueprint_name, "variable_name": variable_name}
    if default_value:
        params["default_value"] = default_value
    if category:
        params["category"] = category
    return json.dumps(send_command("set_blueprint_variable_properties", params))


@mcp.tool()
def add_event_node(blueprint_name: str, event_name: str) -> str:
    """Add an event node (ReceiveBeginPlay, ReceiveTick, ReceiveActorBeginOverlap, etc.)."""
    return json.dumps(send_command("add_event_node", {"blueprint_name": blueprint_name, "event_name": event_name}))


@mcp.tool()
def set_node_property(blueprint_name: str, node_id: str, property_name: str, property_value: str, function_name: str = "") -> str:
    """Set a property on a blueprint node."""
    params = {"blueprint_name": blueprint_name, "node_id": node_id, "property_name": property_name, "property_value": property_value}
    if function_name:
        params["function_name"] = function_name
    return json.dumps(send_command("set_node_property", params))


@mcp.tool()
def create_function(blueprint_name: str, function_name: str) -> str:
    """Create a new function on a blueprint."""
    return json.dumps(send_command("create_function", {"blueprint_name": blueprint_name, "function_name": function_name}))


@mcp.tool()
def add_function_input(blueprint_name: str, function_name: str, param_name: str, param_type: str) -> str:
    """Add an input parameter to a blueprint function."""
    return json.dumps(send_command("add_function_input", {"blueprint_name": blueprint_name, "function_name": function_name, "param_name": param_name, "param_type": param_type}))


@mcp.tool()
def add_function_output(blueprint_name: str, function_name: str, param_name: str, param_type: str) -> str:
    """Add an output parameter to a blueprint function."""
    return json.dumps(send_command("add_function_output", {"blueprint_name": blueprint_name, "function_name": function_name, "param_name": param_name, "param_type": param_type}))


@mcp.tool()
def delete_function(blueprint_name: str, function_name: str) -> str:
    """Delete a function from a blueprint."""
    return json.dumps(send_command("delete_function", {"blueprint_name": blueprint_name, "function_name": function_name}))


@mcp.tool()
def rename_function(blueprint_name: str, old_name: str, new_name: str) -> str:
    """Rename a function on a blueprint."""
    return json.dumps(send_command("rename_function", {"blueprint_name": blueprint_name, "old_name": old_name, "new_name": new_name}))


# ── Blueprint Analysis ────────────────────────────────────────────────

@mcp.tool()
def read_blueprint_content(blueprint_path: str) -> str:
    """Read blueprint content. blueprint_path example: /Game/Blueprints/BP_Name."""
    return json.dumps(send_command("read_blueprint_content", {"blueprint_path": blueprint_path}))


@mcp.tool()
def analyze_blueprint_graph(blueprint_path: str) -> str:
    """Analyze a blueprint's node graph. Returns all nodes, connections, variables, functions."""
    return json.dumps(send_command("analyze_blueprint_graph", {"blueprint_path": blueprint_path}))


@mcp.tool()
def get_blueprint_variable_details(blueprint_name: str) -> str:
    """Get details of all variables on a blueprint."""
    return json.dumps(send_command("get_blueprint_variable_details", {"blueprint_name": blueprint_name}))


@mcp.tool()
def get_blueprint_function_details(blueprint_name: str) -> str:
    """Get details of all functions on a blueprint."""
    return json.dumps(send_command("get_blueprint_function_details", {"blueprint_name": blueprint_name}))


# ── Materials ─────────────────────────────────────────────────────────

@mcp.tool()
def get_available_materials() -> str:
    """List all available materials in the project."""
    return json.dumps(send_command("get_available_materials"))


@mcp.tool()
def apply_material_to_actor(actor_name: str, material_path: str, slot_index: int = 0) -> str:
    """Apply a material to an actor in the level."""
    return json.dumps(send_command("apply_material_to_actor", {"actor_name": actor_name, "material_path": material_path, "slot_index": slot_index}))


@mcp.tool()
def apply_material_to_blueprint(blueprint_name: str, component_name: str, material_path: str, slot_index: int = 0) -> str:
    """Apply a material to a component in a blueprint."""
    return json.dumps(send_command("apply_material_to_blueprint", {"blueprint_name": blueprint_name, "component_name": component_name, "material_path": material_path, "slot_index": slot_index}))


@mcp.tool()
def get_actor_material_info(actor_name: str) -> str:
    """Get material info for an actor."""
    return json.dumps(send_command("get_actor_material_info", {"actor_name": actor_name}))


@mcp.tool()
def set_mesh_material_color(actor_name: str, color: dict, slot_index: int = 0) -> str:
    """Set a material color on an actor's mesh. color is {r,g,b,a} with 0-1 values."""
    return json.dumps(send_command("set_mesh_material_color", {"actor_name": actor_name, "color": color, "slot_index": slot_index}))


# ── Physics ───────────────────────────────────────────────────────────

@mcp.tool()
def set_physics_properties(actor_name: str, simulate_physics: bool = False, gravity_enabled: bool = True, mass: float = 0) -> str:
    """Set physics properties on an actor."""
    params = {"actor_name": actor_name, "simulate_physics": simulate_physics, "gravity_enabled": gravity_enabled}
    if mass > 0:
        params["mass"] = mass
    return json.dumps(send_command("set_physics_properties", params))


# ── Lighting ──────────────────────────────────────────────────────────

@mcp.tool()
def set_light_properties(actor_name: str, intensity: float = None, color: dict = None, cast_shadows: bool = None,
                         temperature: float = None, attenuation_radius: float = None,
                         inner_cone_angle: float = None, outer_cone_angle: float = None) -> str:
    """Set light properties on a light actor. color is {r,g,b}."""
    params = {"actor_name": actor_name}
    if intensity is not None:
        params["intensity"] = intensity
    if color is not None:
        params["color"] = color
    if cast_shadows is not None:
        params["cast_shadows"] = cast_shadows
    if temperature is not None:
        params["temperature"] = temperature
    if attenuation_radius is not None:
        params["attenuation_radius"] = attenuation_radius
    if inner_cone_angle is not None:
        params["inner_cone_angle"] = inner_cone_angle
    if outer_cone_angle is not None:
        params["outer_cone_angle"] = outer_cone_angle
    return json.dumps(send_command("set_light_properties", params))


@mcp.tool()
def add_text_render_component(actor_name: str, text: str, component_name: str = "", position: dict = None,
                              color: dict = None, world_size: float = 24.0) -> str:
    """Add a UTextRenderComponent to an actor."""
    params = {"actor_name": actor_name, "text": text, "world_size": world_size}
    if component_name:
        params["component_name"] = component_name
    if position:
        params["position"] = position
    if color:
        params["color"] = color
    return json.dumps(send_command("add_text_render_component", params))


# ── Map / Level Operations ────────────────────────────────────────────

@mcp.tool()
def save_current_level() -> str:
    """Save the currently active map."""
    return json.dumps(send_command("save_current_level"))


@mcp.tool()
def save_current_level_as(package_path: str) -> str:
    """Save the current map to a new package path (e.g. /Game/Maps/Map_SystemTest)."""
    return json.dumps(send_command("save_current_level_as", {"package_path": package_path}))


@mcp.tool()
def load_level(map_path: str) -> str:
    """Load a map by path (e.g. /Game/Maps/Map_HubCitadelCity)."""
    return json.dumps(send_command("load_level", {"map_path": map_path}))


@mcp.tool()
def new_blank_level(save_path: str = "") -> str:
    """Create a new blank level. Optionally save to a path."""
    params = {}
    if save_path:
        params["save_path"] = save_path
    return json.dumps(send_command("new_blank_level", params))


# ── World Generation ──────────────────────────────────────────────────

@mcp.tool()
def create_wall(location: dict, length: float = 500, height: float = 300, thickness: float = 20, material: str = "") -> str:
    """Create a wall at a location. location is {x,y,z}."""
    params = {"location": location, "length": length, "height": height, "thickness": thickness}
    if material:
        params["material"] = material
    return json.dumps(send_command("create_wall", params))


@mcp.tool()
def create_staircase(location: dict, num_steps: int = 10, step_width: float = 100, step_height: float = 20, step_depth: float = 30) -> str:
    """Create a staircase at a location."""
    return json.dumps(send_command("create_staircase", {"location": location, "num_steps": num_steps, "step_width": step_width, "step_height": step_height, "step_depth": step_depth}))


@mcp.tool()
def create_arch(location: dict, radius: float = 200, height: float = 300, thickness: float = 30, num_segments: int = 12) -> str:
    """Create an arch at a location."""
    return json.dumps(send_command("create_arch", {"location": location, "radius": radius, "height": height, "thickness": thickness, "num_segments": num_segments}))


@mcp.tool()
def spawn_physics_blueprint_actor(blueprint_name: str, actor_name: str, location: dict = None) -> str:
    """Spawn a physics-enabled blueprint actor."""
    params = {"blueprint_name": blueprint_name, "actor_name": actor_name}
    if location:
        params["location"] = location
    return json.dumps(send_command("spawn_physics_blueprint_actor", params))


# ── Widget Blueprints ─────────────────────────────────────────────────

@mcp.tool()
def create_widget_blueprint(name: str, parent_class: str = "") -> str:
    """Create a UMG Widget Blueprint. parent_class for C++ parents like SBWidget_PlayerHUD."""
    params = {"name": name}
    if parent_class:
        params["parent_class"] = parent_class
    return json.dumps(send_command("create_widget_blueprint", params))


@mcp.tool()
def add_widget_to_canvas(blueprint_name: str, widget_type: str, widget_name: str, parent_widget: str = "") -> str:
    """Add a widget to a widget blueprint's tree. widget_type: TextBlock, ProgressBar, Image, Border, Button, CanvasPanel, HorizontalBox, VerticalBox, Overlay, WidgetSwitcher, SizeBox, Spacer."""
    params = {"blueprint_name": blueprint_name, "widget_type": widget_type, "widget_name": widget_name}
    if parent_widget:
        params["parent_widget"] = parent_widget
    return json.dumps(send_command("add_widget_to_canvas", params))


@mcp.tool()
def set_widget_slot(blueprint_name: str, widget_name: str, position: dict = None, size: dict = None,
                    anchors: dict = None, alignment: dict = None, padding: dict = None, fill: float = None) -> str:
    """Set widget slot properties (CanvasPanel position/size/anchors/alignment or Box padding/fill)."""
    params = {"blueprint_name": blueprint_name, "widget_name": widget_name}
    if position:
        params["position"] = position
    if size:
        params["size"] = size
    if anchors:
        params["anchors"] = anchors
    if alignment:
        params["alignment"] = alignment
    if padding:
        params["padding"] = padding
    if fill is not None:
        params["fill"] = fill
    return json.dumps(send_command("set_widget_slot", params))


@mcp.tool()
def set_widget_appearance(blueprint_name: str, widget_name: str, visibility: str = "", opacity: float = None,
                          text: str = "", font_size: int = None, color: dict = None,
                          fill_color: dict = None, tint: dict = None, background: dict = None) -> str:
    """Set widget appearance (visibility, opacity, text, font_size, color, fill_color, tint, background)."""
    params = {"blueprint_name": blueprint_name, "widget_name": widget_name}
    if visibility:
        params["visibility"] = visibility
    if opacity is not None:
        params["opacity"] = opacity
    if text:
        params["text"] = text
    if font_size is not None:
        params["font_size"] = font_size
    if color:
        params["color"] = color
    if fill_color:
        params["fill_color"] = fill_color
    if tint:
        params["tint"] = tint
    if background:
        params["background"] = background
    return json.dumps(send_command("set_widget_appearance", params))


# ── Generic Passthrough ───────────────────────────────────────────────

@mcp.tool()
def run_unreal_command(command_type: str, params: str = "{}") -> str:
    """Send any raw command to the Unreal MCP plugin. params is a JSON string. Use for commands not covered by specific tools (create_pyramid, create_tower, create_maze, construct_house, construct_mansion, create_castle_fortress, create_suspension_bridge, create_aqueduct, create_town, etc.)."""
    return json.dumps(send_command(command_type, json.loads(params)))


@mcp.tool()
def reparent_blueprint(params: str) -> str:
    """Reparent a blueprint to a new parent class.
    Args:
        params: JSON string with 'blueprint_path' and 'new_parent_class'.
    """
    return json.dumps(send_command("reparent_blueprint", json.loads(params)))


@mcp.tool()
def rename_asset(params: str) -> str:
    """Rename an asset.
    Args:
        params: JSON string with 'source_path' and 'destination_path'.
    """
    return json.dumps(send_command("rename_asset", json.loads(params)))


if __name__ == "__main__":
    mcp.run(transport="stdio")
