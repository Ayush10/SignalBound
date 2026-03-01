# C++ Module & MCP Widget Extension Spec

## Part A: SignalBound C++ Game Module

### Why
The project is Blueprint-only. Adding a C++ module gives us UUserWidget base classes for the HUD, notices, and menu. These C++ classes define the interface (BindWidget, BlueprintCallable functions) that Widget Blueprints inherit from.

### Directory Structure
```
Source/
├── SignalBound.Target.cs
├── SignalBoundEditor.Target.cs
└── SignalBound/
    ├── SignalBound.Build.cs
    ├── Public/
    │   ├── SignalBoundModule.h
    │   └── UI/
    │       ├── SBWidget_PlayerHUD.h
    │       ├── SBWidget_SystemNotice.h
    │       └── SBWidget_SystemMenu.h
    └── Private/
        ├── SignalBoundModule.cpp
        └── UI/
            ├── SBWidget_PlayerHUD.cpp
            ├── SBWidget_SystemNotice.cpp
            └── SBWidget_SystemMenu.cpp
```

### .uproject Change
Add before "Plugins":
```json
"Modules": [
    {
        "Name": "SignalBound",
        "Type": "Runtime",
        "LoadingPhase": "Default"
    }
],
```

### Build.cs Dependencies
```
Public: Core, CoreUObject, Engine, InputCore, UMG, Slate, SlateCore
Private: Kismet
```

### Target Files
Both use `BuildSettingsVersion.Latest`, `IncludeOrderVersion.Latest`, `ExtraModuleNames.Add("SignalBound")`
- SignalBound.Target.cs: `Type = TargetType.Game`
- SignalBoundEditor.Target.cs: `Type = TargetType.Editor`

### Widget Classes

**USBWidget_PlayerHUD** (extends UUserWidget)
```cpp
UPROPERTY(meta=(BindWidget)) UProgressBar* HealthBar;
UPROPERTY(meta=(BindWidget)) UProgressBar* StaminaBar;
UPROPERTY(meta=(BindWidget)) UImage* CooldownArc;
UPROPERTY(meta=(BindWidget)) UImage* SkillIcon;

UFUNCTION(BlueprintCallable) void UpdateHealth(float Pct);
UFUNCTION(BlueprintCallable) void UpdateStamina(float Pct);
UFUNCTION(BlueprintCallable) void UpdateCooldown(float Pct);

// NativeTick for smooth bar interpolation
float TargetHealth, TargetStamina, TargetCooldown;
float InterpSpeed = 10.0f;
```

**USBWidget_SystemNotice** (extends UUserWidget)
```cpp
UPROPERTY(meta=(BindWidget)) UTextBlock* NoticeText;
UPROPERTY(meta=(BindWidget)) UBorder* NoticePanel;

UFUNCTION(BlueprintCallable) void ShowNotice(const FString& Text, float Duration = 3.0f);
UFUNCTION(BlueprintCallable) void HideNotice();

UFUNCTION(BlueprintImplementableEvent) void OnNoticeShown();
UFUNCTION(BlueprintImplementableEvent) void OnNoticeHidden();

float DisplayTimer;
bool bIsShowing;
FTimerHandle HideTimerHandle;
```

**USBWidget_SystemMenu** (extends UUserWidget)
```cpp
UPROPERTY(meta=(BindWidget)) UWidgetSwitcher* TabSwitcher;
UPROPERTY(meta=(BindWidget)) UWidget* StatusPanel;
UPROPERTY(meta=(BindWidget)) UWidget* ContractsPanel;
UPROPERTY(meta=(BindWidget)) UWidget* SkillsPanel;
UPROPERTY(meta=(BindWidget)) UButton* TabButton_Status;
UPROPERTY(meta=(BindWidget)) UButton* TabButton_Contracts;
UPROPERTY(meta=(BindWidget)) UButton* TabButton_Skills;

UFUNCTION(BlueprintCallable) void SelectTab(int32 Index);
UFUNCTION(BlueprintCallable) void OpenMenu();
UFUNCTION(BlueprintCallable) void CloseMenu();

UFUNCTION(BlueprintImplementableEvent) void OnMenuOpened();
UFUNCTION(BlueprintImplementableEvent) void OnMenuClosed();

int32 CurrentTab = 0;
bool bIsOpen = false;
```

### After File Creation
1. Regenerate project files: right-click .uproject → "Generate Xcode Project" (macOS) or use UBT
2. Compile via Xcode or reopen in editor (auto-compiles)
3. The SIGNALBOUND_API macro requires the module name matches

---

## Part B: MCP Widget Extension

### New Files
```
Plugins/UnrealMCP/Source/UnrealMCP/
├── Public/Commands/EpicUnrealMCPWidgetCommands.h
└── Private/Commands/EpicUnrealMCPWidgetCommands.cpp
```

### New Commands

**create_widget_blueprint**
- Params: `name` (string), `parent_class` (string, default "UserWidget")
- Uses UWidgetBlueprintFactory (from UMGEditor module)
- Factory->ParentClass = UUserWidget or our C++ subclass
- Creates at `/Game/SignalBound/UI/{name}`

**add_widget_to_canvas**
- Params: `widget_bp_name`, `widget_class` (TextBlock/ProgressBar/Image/Border/Button/CanvasPanel/VerticalBox/HorizontalBox/WidgetSwitcher/Overlay), `widget_name`, `slot_properties{}`
- Accesses the Widget Blueprint's WidgetTree
- Creates UWidget instance, adds to tree under root or specified parent

**set_widget_slot**
- Params: `widget_bp_name`, `widget_name`, `slot_type` (CanvasSlot/HorizontalBoxSlot/VerticalBoxSlot), `properties{}`
- For CanvasSlot: anchors, position, size, alignment
- For Box slots: padding, fill, alignment

**set_widget_appearance**
- Params: `widget_bp_name`, `widget_name`, `properties{}`
- Color tint, opacity, font size, brush, visibility, text content

### Bridge Registration
Add to EpicUnrealMCPBridge.h: `TSharedPtr<FEpicUnrealMCPWidgetCommands> WidgetCommands;`
Add to ExecuteCommand dispatch: check for "create_widget_blueprint", "add_widget_to_canvas", "set_widget_slot", "set_widget_appearance"

### Build.cs Addition
Add `"UMG"` and `"UMGEditor"` to PublicDependencyModuleNames

### Python MCP Server Addition
Add 4 new `@mcp.tool()` functions in unreal_mcp_server_advanced.py that call the new commands via TCP

### Key UE5 Widget Blueprint Internals
- Widget Blueprints use `UWidgetBlueprintFactory` (not `UBlueprintFactory`)
- Widget hierarchy is managed via `UWidgetTree` (not SimpleConstructionScript)
- Root widget is typically a CanvasPanel or Overlay
- `BindWidget` meta expects the WBP to have a widget with matching name
- Compilation uses same `FKismetEditorUtilities::CompileBlueprint()`
