# UnrealMCP Capabilities Reference

## Overview
MCP (Model Context Protocol) server that lets Claude Code control Unreal Engine 5.7 in real-time.
Architecture: `Claude Code → MCP Protocol → Python Server → TCP (port 55557) → C++ Plugin → Unreal Editor`

## MCP Server Location
- Python server: `/Users/ayushojha/Desktop/03_Projects/unreal/unreal-engine-mcp/Python/unreal_mcp_server_advanced.py`
- Plugin: `Plugins/UnrealMCP/Source/UnrealMCP/`

## All 43 MCP Tools

### Actor/Level Management (6)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_actors_in_level` | (none) | List all actors in current level |
| `find_actors_by_name` | pattern | Search actors by name |
| `delete_actor` | name | Delete actor by name |
| `set_actor_transform` | name, location[], rotation[], scale[] | Set position/rotation/scale |
| `spawn_physics_blueprint_actor` | name, mesh_path, location, mass, simulate_physics | Spawn BP with physics |
| `compile_blueprint` | blueprint_name | Compile a Blueprint |

### Blueprint Creation (3)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `create_blueprint` | name, parent_class | Create new BP (parent: "Actor", "Character", "Pawn", "GameModeBase", etc.) |
| `add_component_to_blueprint` | blueprint_name, component_type, component_name, location[], rotation[], scale[], component_properties{} | Add any UE component |
| `set_static_mesh_properties` | blueprint_name, component_name, static_mesh_path | Assign mesh to component |

### Blueprint Graph (11)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `add_node` | blueprint_name, node_type, node_params{} | Add node (23 types) |
| `connect_nodes` | blueprint_name, source_node_id, source_pin_name, target_node_id, target_pin_name, function_name? | Connect pins |
| `create_variable` | blueprint_name, variable_name, variable_type, default_value?, is_public?, tooltip?, category? | Create variable |
| `set_blueprint_variable_properties` | blueprint_name, variable_name, (20+ properties) | Modify variable |
| `add_event_node` | blueprint_name, event_name, pos_x, pos_y | Add event (BeginPlay, Tick, etc.) |
| `delete_node` | blueprint_name, node_id, function_name? | Remove node |
| `set_node_property` | blueprint_name, node_id, property_name, property_value, action? | Modify node |
| `create_function` | blueprint_name, function_name, return_type? | Create function |
| `add_function_input` | blueprint_name, function_name, param_name, param_type, is_array? | Add function param |
| `add_function_output` | blueprint_name, function_name, param_name, param_type, is_array? | Add return param |
| `delete_function` / `rename_function` | blueprint_name, function_name | Manage functions |

### Blueprint Analysis (4)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `read_blueprint_content` | blueprint_path | Raw BP content as JSON |
| `analyze_blueprint_graph` | blueprint_path, graph_name? | Graph structure analysis |
| `get_blueprint_variable_details` | blueprint_path, variable_name? | Variable info |
| `get_blueprint_function_details` | blueprint_path, function_name? | Function signatures |

### Materials (5)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_available_materials` | search_path?, include_engine? | List materials |
| `apply_material_to_actor` | actor_name, material_path, slot_index? | Apply to actor |
| `apply_material_to_blueprint` | blueprint_name, component_name, material_path | Apply to BP |
| `get_actor_material_info` | actor_name | Query materials |
| `set_mesh_material_color` | blueprint_name, component_name, color[] | Set color |

### Physics (1)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `set_physics_properties` | blueprint_name, component_name, simulate_physics, gravity_enabled, mass, linear_damping, angular_damping | Configure physics |

### World Generation (9)
`create_pyramid`, `create_wall`, `create_tower`, `create_staircase`, `create_arch`, `create_maze`, `construct_house`, `construct_mansion`, `create_castle_fortress`, `create_suspension_bridge`, `create_aqueduct`, `create_town`

## 23 Node Types for add_node

### Control Flow
| Type | K2Node Class | Key Params |
|------|-------------|------------|
| `Branch` | K2Node_IfThenElse | pos_x, pos_y |
| `Comparison` | K2Node_PromotableOperator | comparison_type (==,!=,<,>,AND,OR,XOR) |
| `Switch` | K2Node_Switch | — |
| `SwitchEnum` | K2Node_SwitchEnum | enum_type |
| `SwitchInteger` | K2Node_SwitchInteger | — |
| `ExecutionSequence` | K2Node_ExecutionSequence | — |
| `Select` | K2Node_Select | — |

### Data
| Type | Key Params |
|------|------------|
| `VariableGet` | variable_name |
| `VariableSet` | variable_name |
| `MakeArray` | — |

### Utility
| Type | Key Params |
|------|------------|
| `Print` | message |
| `CallFunction` | target_function, target_blueprint? |
| `SpawnActor` | — |
| `Self` | — |

### Casting
| Type | Key Params |
|------|------------|
| `DynamicCast` | cast_class |
| `ClassDynamicCast` | cast_class |
| `CastByteToEnum` | enum_type |

### Events
| Type | Key Params |
|------|------------|
| `Event` | event_type (BeginPlay, Tick, etc.) |

### Specialized
| Type | Key Params | Notes |
|------|------------|-------|
| `Timeline` | — | Creates node only, curves must be added manually |
| `GetDataTableRow` | data_table_path | DataTable must exist |
| `AddComponentByClass` | — | Dynamic component add |
| `ConstructObject` | — | Create object instance |
| `Knot` | — | Wire reroute node |

## Pin Connection Conventions

- **Execution pins**: source `"execute"` → target `"execute"` (or `"Then"` for Branch true, `"Else"` for false)
- **Variable Get output**: pin name = variable name (e.g., `"CurrentHealth"`)
- **Variable Set input**: pin name = variable name
- **Print node input**: `"InString"`
- **Branch condition**: `"Condition"`
- **CallFunction**: pin names match function parameter names
- **SwitchInteger**: output pins are `"0"`, `"1"`, `"2"`, etc. + `"Default"`
- **function_name** parameter: if provided, adds node to that function's graph instead of EventGraph

## Variable Types
`bool`, `int`, `float`, `string`, `vector` ([x,y,z]), `rotator` ([pitch,yaw,roll])

## Variable Properties (20+)
`var_name`, `var_type`, `is_blueprint_readable`, `is_blueprint_writable`, `is_public`, `is_editable_in_instance`, `tooltip`, `category`, `default_value`, `expose_on_spawn`, `expose_to_cinematics`, `slider_range_min/max`, `value_range_min/max`, `replication_enabled`, `replication_condition` (0-7)

## What MCP CANNOT Do
- Create Widget Blueprints (UMG) — **solved via C++ extension (Step 0B)**
- Create DataAssets or DataTables
- Create custom Enums or Structs
- Create Materials or Material Instances
- Edit Timeline animation curves
- Create/edit Animation Blueprints or State Machines
- Create Behavior Trees or Blackboards
- Reference asset objects (IA_, AnimMontage) in CallFunction nodes
- Set `is_private` on variables (bug)

## Component Types (commonly used)
`StaticMeshComponent`, `SkeletalMeshComponent`, `BoxComponent`, `SphereComponent`, `CapsuleComponent`, `SpringArmComponent`, `CameraComponent`, `ArrowComponent`, `AudioComponent`, `PointLightComponent`, `SpotLightComponent`
