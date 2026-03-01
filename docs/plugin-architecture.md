# UnrealMCP Plugin Architecture

## Command Flow
```
Python MCP Server (port 55557 TCP)
    ↓ JSON: {"type": "command_name", "params": {...}}
MCPServerRunnable (TCP listener thread)
    ↓
UEpicUnrealMCPBridge::ExecuteCommand() [GameThread via AsyncTask]
    ↓ if-else chain on CommandType string
    ├─ FEpicUnrealMCPEditorCommands    → actors, spawning, transforms
    ├─ FEpicUnrealMCPBlueprintCommands → BP creation, components, materials
    ├─ FEpicUnrealMCPBlueprintGraphCommands → nodes, connections, variables, functions
    └─ FEpicUnrealMCPWidgetCommands    → [TO BE ADDED] widget blueprint creation
    ↓
JSON Response: {"success": true/false, "result": {...}, "error": "..."}
```

## File Structure
```
Plugins/UnrealMCP/Source/UnrealMCP/
├── UnrealMCP.Build.cs
├── Public/
│   ├── EpicUnrealMCPModule.h
│   ├── EpicUnrealMCPBridge.h
│   ├── MCPServerRunnable.h
│   ├── Commands/
│   │   ├── EpicUnrealMCPEditorCommands.h
│   │   ├── EpicUnrealMCPBlueprintCommands.h
│   │   ├── EpicUnrealMCPBlueprintGraphCommands.h
│   │   ├── EpicUnrealMCPCommonUtils.h
│   │   └── BlueprintGraph/
│   │       ├── BPConnector.h
│   │       ├── BPVariables.h
│   │       ├── EventManager.h
│   │       ├── NodeManager.h
│   │       ├── NodeDeleter.h
│   │       ├── NodePropertyManager.h
│   │       ├── Function/FunctionManager.h
│   │       ├── Function/FunctionIO.h
│   │       └── Nodes/ (ControlFlowNodes, DataNodes, UtilityNodes, CastingNodes, AnimationNodes, SpecializedNodes, NodeCreatorUtils)
└── Private/
    ├── EpicUnrealMCPModule.cpp
    ├── EpicUnrealMCPBridge.cpp
    ├── MCPServerRunnable.cpp
    └── Commands/ (matching .cpp files)
```

## How to Add a New Command

### 1. Create Handler Class
```cpp
// Public/Commands/EpicUnrealMCPWidgetCommands.h
class FEpicUnrealMCPWidgetCommands
{
public:
    TSharedPtr<FJsonObject> HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);
private:
    TSharedPtr<FJsonObject> HandleCreateWidgetBlueprint(const TSharedPtr<FJsonObject>& Params);
    // ... more handlers
};
```

### 2. Register in Bridge (EpicUnrealMCPBridge.cpp)
```cpp
// In constructor:
WidgetCommands = MakeShared<FEpicUnrealMCPWidgetCommands>();

// In ExecuteCommand:
else if (CommandType == TEXT("create_widget_blueprint") || ...)
    ResultJson = WidgetCommands->HandleCommand(CommandType, Params);
```

### 3. Add Python MCP Tool
```python
@mcp.tool()
def create_widget_blueprint(name: str, parent_class: str = "UserWidget") -> Dict[str, Any]:
    unreal = get_unreal_connection()
    return unreal.send_command("create_widget_blueprint", {"name": name, "parent_class": parent_class})
```

## Build.cs Current Dependencies
**Public:** Core, CoreUObject, Engine, InputCore, Networking, Sockets, HTTP, Json, JsonUtilities, DeveloperSettings, PhysicsCore, UnrealEd, BlueprintGraph, KismetCompiler
**Private:** EditorScriptingUtilities, EditorSubsystem, Slate, SlateCore, Kismet, Projects, AssetRegistry
**Editor-only:** PropertyEditor, ToolMenus, BlueprintEditorLibrary

**To add for widgets:** `UMG`, `UMGEditor` in PublicDependencyModuleNames

## Blueprint Creation Pattern (create_blueprint)
```cpp
UBlueprintFactory* Factory = NewObject<UBlueprintFactory>();
Factory->ParentClass = UClass; // AActor, UUserWidget, etc.
UPackage* Package = CreatePackage(*PackagePath);
UBlueprint* BP = Cast<UBlueprint>(Factory->FactoryCreateNew(...));
FAssetRegistryModule::AssetCreated(BP);
Package->MarkPackageDirty();
```

## Response Format
```json
// Success:
{"success": true, "data": {"name": "MyBP", "path": "/Game/Blueprints/MyBP"}}
// Error:
{"success": false, "error": "Missing 'name' parameter"}
```

## Connection Config
- Host: 127.0.0.1, Port: 55557
- Buffer: 8192 bytes (recv), 131072 bytes (socket)
- Retry: 3 attempts, exponential backoff
- Timeout: 30s default, 300s for large ops (towns, castles, mazes)
- Thread-safe with RLock, commands execute on GameThread
