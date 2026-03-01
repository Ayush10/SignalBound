#include "Commands/EpicUnrealMCPWidgetCommands.h"
#include "Commands/EpicUnrealMCPCommonUtils.h"
#include "EditorAssetLibrary.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"

// Widget Blueprint includes
#include "WidgetBlueprint.h"
#include "WidgetBlueprintFactory.h"
#include "Blueprint/UserWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/WidgetSwitcher.h"
#include "Components/TextBlock.h"
#include "Components/ProgressBar.h"
#include "Components/Image.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"

FEpicUnrealMCPWidgetCommands::FEpicUnrealMCPWidgetCommands()
{
}

TSharedPtr<FJsonObject> FEpicUnrealMCPWidgetCommands::HandleCommand(
	const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
	if (CommandType == TEXT("create_widget_blueprint"))
	{
		return HandleCreateWidgetBlueprint(Params);
	}
	else if (CommandType == TEXT("add_widget_to_canvas"))
	{
		return HandleAddWidgetToCanvas(Params);
	}
	else if (CommandType == TEXT("set_widget_slot"))
	{
		return HandleSetWidgetSlot(Params);
	}
	else if (CommandType == TEXT("set_widget_appearance"))
	{
		return HandleSetWidgetAppearance(Params);
	}

	return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
		FString::Printf(TEXT("Unknown widget command: %s"), *CommandType));
}

// ============================================================================
// Create Widget Blueprint
// ============================================================================
TSharedPtr<FJsonObject> FEpicUnrealMCPWidgetCommands::HandleCreateWidgetBlueprint(
	const TSharedPtr<FJsonObject>& Params)
{
	FString WidgetName;
	if (!Params->TryGetStringField(TEXT("name"), WidgetName))
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
	}

	FString ParentClassName;
	if (!Params->TryGetStringField(TEXT("parent_class"), ParentClassName))
	{
		ParentClassName = TEXT("UserWidget");
	}

	FString PackagePath = TEXT("/Game/SignalBound/UI/");

	// Check if already exists
	FString FullPath = PackagePath + WidgetName;
	if (UEditorAssetLibrary::DoesAssetExist(FullPath))
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Widget blueprint '%s' already exists"), *WidgetName));
	}

	// Resolve parent class
	UClass* ParentClass = UUserWidget::StaticClass();

	if (!ParentClassName.Equals(TEXT("UserWidget"), ESearchCase::IgnoreCase))
	{
		// Try to find the class - check common paths
		UClass* FoundClass = nullptr;

		// Try /Script/UMG path
		FString ClassPath = FString::Printf(TEXT("/Script/UMG.%s"), *ParentClassName);
		FoundClass = LoadClass<UUserWidget>(nullptr, *ClassPath);

		if (!FoundClass)
		{
			// Try /Script/SignalBound path (our C++ module)
			ClassPath = FString::Printf(TEXT("/Script/SignalBound.%s"), *ParentClassName);
			FoundClass = LoadClass<UUserWidget>(nullptr, *ClassPath);
		}

		if (!FoundClass)
		{
			// Try with U prefix stripped or added
			FString AdjustedName = ParentClassName;
			if (AdjustedName.StartsWith(TEXT("U")))
			{
				AdjustedName = AdjustedName.RightChop(1);
			}
			ClassPath = FString::Printf(TEXT("/Script/SignalBound.%s"), *AdjustedName);
			FoundClass = LoadClass<UUserWidget>(nullptr, *ClassPath);
		}

		if (!FoundClass)
		{
			// Try FindFirstObject as fallback
			FoundClass = FindFirstObject<UClass>(*ParentClassName, EFindFirstObjectOptions::NativeFirst);
			if (FoundClass && !FoundClass->IsChildOf(UUserWidget::StaticClass()))
			{
				FoundClass = nullptr;
			}
		}

		if (FoundClass)
		{
			ParentClass = FoundClass;
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("Could not find parent class '%s', falling back to UUserWidget"), *ParentClassName);
		}
	}

	// Create the widget blueprint using the factory
	UWidgetBlueprintFactory* Factory = NewObject<UWidgetBlueprintFactory>();
	Factory->ParentClass = ParentClass;

	UPackage* Package = CreatePackage(*FullPath);
	if (!Package)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create package"));
	}

	UWidgetBlueprint* NewWidgetBP = Cast<UWidgetBlueprint>(
		Factory->FactoryCreateNew(
			UWidgetBlueprint::StaticClass(),
			Package,
			*WidgetName,
			RF_Standalone | RF_Public,
			nullptr,
			GWarn
		)
	);

	if (!NewWidgetBP)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create widget blueprint"));
	}

	// Notify asset registry
	FAssetRegistryModule::AssetCreated(NewWidgetBP);
	Package->MarkPackageDirty();

	// Add a root CanvasPanel if the widget tree is empty
	if (NewWidgetBP->WidgetTree)
	{
		UWidget* RootWidget = NewWidgetBP->WidgetTree->RootWidget;
		if (!RootWidget)
		{
			UCanvasPanel* Canvas = NewWidgetBP->WidgetTree->ConstructWidget<UCanvasPanel>(
				UCanvasPanel::StaticClass(), TEXT("RootCanvas"));
			NewWidgetBP->WidgetTree->RootWidget = Canvas;
		}
	}

	// Compile
	FKismetEditorUtilities::CompileBlueprint(NewWidgetBP);

	TSharedPtr<FJsonObject> Result = MakeShareable(new FJsonObject);
	Result->SetBoolField(TEXT("success"), true);
	Result->SetStringField(TEXT("name"), WidgetName);
	Result->SetStringField(TEXT("path"), FullPath);
	Result->SetStringField(TEXT("parent_class"), ParentClass->GetName());
	return Result;
}

// ============================================================================
// Add Widget to Canvas/Tree
// ============================================================================
TSharedPtr<FJsonObject> FEpicUnrealMCPWidgetCommands::HandleAddWidgetToCanvas(
	const TSharedPtr<FJsonObject>& Params)
{
	FString WidgetBPName;
	if (!Params->TryGetStringField(TEXT("widget_bp_name"), WidgetBPName))
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_bp_name'"));
	}

	FString WidgetClassName;
	if (!Params->TryGetStringField(TEXT("widget_class"), WidgetClassName))
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_class'"));
	}

	FString WidgetName;
	if (!Params->TryGetStringField(TEXT("widget_name"), WidgetName))
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_name'"));
	}

	FString ParentWidgetName;
	Params->TryGetStringField(TEXT("parent_widget"), ParentWidgetName);

	// Find the widget blueprint
	UWidgetBlueprint* WidgetBP = FindWidgetBlueprint(WidgetBPName);
	if (!WidgetBP)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Widget blueprint '%s' not found"), *WidgetBPName));
	}

	if (!WidgetBP->WidgetTree)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Widget blueprint has no widget tree"));
	}

	// Map class name string to actual UClass
	UClass* TargetClass = nullptr;

	// Common widget class mapping
	static TMap<FString, UClass*> WidgetClassMap;
	if (WidgetClassMap.Num() == 0)
	{
		WidgetClassMap.Add(TEXT("TextBlock"), UTextBlock::StaticClass());
		WidgetClassMap.Add(TEXT("ProgressBar"), UProgressBar::StaticClass());
		WidgetClassMap.Add(TEXT("Image"), UImage::StaticClass());
		WidgetClassMap.Add(TEXT("Border"), UBorder::StaticClass());
		WidgetClassMap.Add(TEXT("Button"), UButton::StaticClass());
		WidgetClassMap.Add(TEXT("CanvasPanel"), UCanvasPanel::StaticClass());
		WidgetClassMap.Add(TEXT("HorizontalBox"), UHorizontalBox::StaticClass());
		WidgetClassMap.Add(TEXT("VerticalBox"), UVerticalBox::StaticClass());
		WidgetClassMap.Add(TEXT("Overlay"), UOverlay::StaticClass());
		WidgetClassMap.Add(TEXT("WidgetSwitcher"), UWidgetSwitcher::StaticClass());
		WidgetClassMap.Add(TEXT("SizeBox"), USizeBox::StaticClass());
		WidgetClassMap.Add(TEXT("Spacer"), USpacer::StaticClass());
	}

	if (UClass** Found = WidgetClassMap.Find(WidgetClassName))
	{
		TargetClass = *Found;
	}
	else
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Unknown widget class: %s. Supported: TextBlock, ProgressBar, Image, Border, Button, CanvasPanel, HorizontalBox, VerticalBox, Overlay, WidgetSwitcher, SizeBox, Spacer"), *WidgetClassName));
	}

	// Create the widget
	UWidget* NewWidget = WidgetBP->WidgetTree->ConstructWidget<UWidget>(TargetClass, *WidgetName);
	if (!NewWidget)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to construct widget"));
	}

	// Find parent panel to add to
	UPanelWidget* ParentPanel = nullptr;
	if (ParentWidgetName.IsEmpty())
	{
		// Add to root
		ParentPanel = Cast<UPanelWidget>(WidgetBP->WidgetTree->RootWidget);
	}
	else
	{
		UWidget* ParentWidget = FindWidgetInTree(WidgetBP, ParentWidgetName);
		ParentPanel = Cast<UPanelWidget>(ParentWidget);
	}

	if (!ParentPanel)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Parent panel '%s' not found or is not a panel widget"),
				ParentWidgetName.IsEmpty() ? TEXT("Root") : *ParentWidgetName));
	}

	// Add to parent
	UPanelSlot* Slot = ParentPanel->AddChild(NewWidget);
	if (!Slot)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to add widget to parent panel"));
	}

	// Mark dirty and compile
	WidgetBP->MarkPackageDirty();
	FKismetEditorUtilities::CompileBlueprint(WidgetBP);

	TSharedPtr<FJsonObject> Result = MakeShareable(new FJsonObject);
	Result->SetBoolField(TEXT("success"), true);
	Result->SetStringField(TEXT("widget_name"), WidgetName);
	Result->SetStringField(TEXT("widget_class"), WidgetClassName);
	Result->SetStringField(TEXT("parent"), ParentWidgetName.IsEmpty() ? TEXT("Root") : ParentWidgetName);
	return Result;
}

// ============================================================================
// Set Widget Slot Properties
// ============================================================================
TSharedPtr<FJsonObject> FEpicUnrealMCPWidgetCommands::HandleSetWidgetSlot(
	const TSharedPtr<FJsonObject>& Params)
{
	FString WidgetBPName;
	if (!Params->TryGetStringField(TEXT("widget_bp_name"), WidgetBPName))
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_bp_name'"));
	}

	FString WidgetName;
	if (!Params->TryGetStringField(TEXT("widget_name"), WidgetName))
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_name'"));
	}

	UWidgetBlueprint* WidgetBP = FindWidgetBlueprint(WidgetBPName);
	if (!WidgetBP)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Widget blueprint not found"));
	}

	UWidget* Widget = FindWidgetInTree(WidgetBP, WidgetName);
	if (!Widget)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Widget '%s' not found in tree"), *WidgetName));
	}

	UPanelSlot* Slot = Widget->Slot;
	if (!Slot)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Widget has no slot"));
	}

	const TSharedPtr<FJsonObject>* PropsPtr;
	if (!Params->TryGetObjectField(TEXT("properties"), PropsPtr) || !PropsPtr)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'properties' object"));
	}
	const TSharedPtr<FJsonObject>& Props = *PropsPtr;

	// Handle CanvasPanelSlot
	if (UCanvasPanelSlot* CanvasSlot = Cast<UCanvasPanelSlot>(Slot))
	{
		// Position
		if (Props->HasField(TEXT("position_x")) || Props->HasField(TEXT("position_y")))
		{
			FVector2D Pos = CanvasSlot->GetPosition();
			if (Props->HasField(TEXT("position_x"))) Pos.X = Props->GetNumberField(TEXT("position_x"));
			if (Props->HasField(TEXT("position_y"))) Pos.Y = Props->GetNumberField(TEXT("position_y"));
			CanvasSlot->SetPosition(Pos);
		}

		// Size
		if (Props->HasField(TEXT("size_x")) || Props->HasField(TEXT("size_y")))
		{
			FVector2D Size = CanvasSlot->GetSize();
			if (Props->HasField(TEXT("size_x"))) Size.X = Props->GetNumberField(TEXT("size_x"));
			if (Props->HasField(TEXT("size_y"))) Size.Y = Props->GetNumberField(TEXT("size_y"));
			CanvasSlot->SetSize(Size);
		}

		// Anchors
		if (Props->HasField(TEXT("anchor_min_x")) || Props->HasField(TEXT("anchor_min_y")) ||
			Props->HasField(TEXT("anchor_max_x")) || Props->HasField(TEXT("anchor_max_y")))
		{
			FAnchors Anchors = CanvasSlot->GetAnchors();
			if (Props->HasField(TEXT("anchor_min_x"))) Anchors.Minimum.X = Props->GetNumberField(TEXT("anchor_min_x"));
			if (Props->HasField(TEXT("anchor_min_y"))) Anchors.Minimum.Y = Props->GetNumberField(TEXT("anchor_min_y"));
			if (Props->HasField(TEXT("anchor_max_x"))) Anchors.Maximum.X = Props->GetNumberField(TEXT("anchor_max_x"));
			if (Props->HasField(TEXT("anchor_max_y"))) Anchors.Maximum.Y = Props->GetNumberField(TEXT("anchor_max_y"));
			CanvasSlot->SetAnchors(Anchors);
		}

		// Alignment
		if (Props->HasField(TEXT("alignment_x")) || Props->HasField(TEXT("alignment_y")))
		{
			FVector2D Alignment = CanvasSlot->GetAlignment();
			if (Props->HasField(TEXT("alignment_x"))) Alignment.X = Props->GetNumberField(TEXT("alignment_x"));
			if (Props->HasField(TEXT("alignment_y"))) Alignment.Y = Props->GetNumberField(TEXT("alignment_y"));
			CanvasSlot->SetAlignment(Alignment);
		}

		// Auto size
		if (Props->HasField(TEXT("auto_size")))
		{
			CanvasSlot->SetAutoSize(Props->GetBoolField(TEXT("auto_size")));
		}
	}
	// Handle HorizontalBoxSlot
	else if (UHorizontalBoxSlot* HBoxSlot = Cast<UHorizontalBoxSlot>(Slot))
	{
		if (Props->HasField(TEXT("padding")))
		{
			float Pad = Props->GetNumberField(TEXT("padding"));
			HBoxSlot->SetPadding(FMargin(Pad));
		}
		if (Props->HasField(TEXT("fill_width")))
		{
			float Fill = Props->GetNumberField(TEXT("fill_width"));
			FSlateChildSize Size(ESlateSizeRule::Fill);
			HBoxSlot->SetSize(Size);
		}
	}
	// Handle VerticalBoxSlot
	else if (UVerticalBoxSlot* VBoxSlot = Cast<UVerticalBoxSlot>(Slot))
	{
		if (Props->HasField(TEXT("padding")))
		{
			float Pad = Props->GetNumberField(TEXT("padding"));
			VBoxSlot->SetPadding(FMargin(Pad));
		}
	}

	WidgetBP->MarkPackageDirty();
	FKismetEditorUtilities::CompileBlueprint(WidgetBP);

	TSharedPtr<FJsonObject> Result = MakeShareable(new FJsonObject);
	Result->SetBoolField(TEXT("success"), true);
	Result->SetStringField(TEXT("widget_name"), WidgetName);
	return Result;
}

// ============================================================================
// Set Widget Appearance
// ============================================================================
TSharedPtr<FJsonObject> FEpicUnrealMCPWidgetCommands::HandleSetWidgetAppearance(
	const TSharedPtr<FJsonObject>& Params)
{
	FString WidgetBPName;
	if (!Params->TryGetStringField(TEXT("widget_bp_name"), WidgetBPName))
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_bp_name'"));
	}

	FString WidgetName;
	if (!Params->TryGetStringField(TEXT("widget_name"), WidgetName))
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'widget_name'"));
	}

	UWidgetBlueprint* WidgetBP = FindWidgetBlueprint(WidgetBPName);
	if (!WidgetBP)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Widget blueprint not found"));
	}

	UWidget* Widget = FindWidgetInTree(WidgetBP, WidgetName);
	if (!Widget)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
			FString::Printf(TEXT("Widget '%s' not found"), *WidgetName));
	}

	const TSharedPtr<FJsonObject>* PropsPtr;
	if (!Params->TryGetObjectField(TEXT("properties"), PropsPtr) || !PropsPtr)
	{
		return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'properties' object"));
	}
	const TSharedPtr<FJsonObject>& Props = *PropsPtr;

	// Visibility
	if (Props->HasField(TEXT("visibility")))
	{
		FString Vis = Props->GetStringField(TEXT("visibility"));
		if (Vis == TEXT("Visible")) Widget->SetVisibility(ESlateVisibility::Visible);
		else if (Vis == TEXT("Hidden")) Widget->SetVisibility(ESlateVisibility::Hidden);
		else if (Vis == TEXT("Collapsed")) Widget->SetVisibility(ESlateVisibility::Collapsed);
		else if (Vis == TEXT("HitTestInvisible")) Widget->SetVisibility(ESlateVisibility::HitTestInvisible);
		else if (Vis == TEXT("SelfHitTestInvisible")) Widget->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	}

	// Opacity
	if (Props->HasField(TEXT("opacity")))
	{
		Widget->SetRenderOpacity(Props->GetNumberField(TEXT("opacity")));
	}

	// TextBlock-specific
	if (UTextBlock* TextBlock = Cast<UTextBlock>(Widget))
	{
		if (Props->HasField(TEXT("text")))
		{
			TextBlock->SetText(FText::FromString(Props->GetStringField(TEXT("text"))));
		}
		if (Props->HasField(TEXT("font_size")))
		{
			FSlateFontInfo FontInfo = TextBlock->GetFont();
			FontInfo.Size = static_cast<int32>(Props->GetNumberField(TEXT("font_size")));
			TextBlock->SetFont(FontInfo);
		}
		if (Props->HasField(TEXT("color_r")) || Props->HasField(TEXT("color_g")) || Props->HasField(TEXT("color_b")))
		{
			float R = Props->HasField(TEXT("color_r")) ? Props->GetNumberField(TEXT("color_r")) : 1.0f;
			float G = Props->HasField(TEXT("color_g")) ? Props->GetNumberField(TEXT("color_g")) : 1.0f;
			float B = Props->HasField(TEXT("color_b")) ? Props->GetNumberField(TEXT("color_b")) : 1.0f;
			float A = Props->HasField(TEXT("color_a")) ? Props->GetNumberField(TEXT("color_a")) : 1.0f;
			TextBlock->SetColorAndOpacity(FSlateColor(FLinearColor(R, G, B, A)));
		}
		if (Props->HasField(TEXT("justification")))
		{
			FString Just = Props->GetStringField(TEXT("justification"));
			if (Just == TEXT("Left")) TextBlock->SetJustification(ETextJustify::Left);
			else if (Just == TEXT("Center")) TextBlock->SetJustification(ETextJustify::Center);
			else if (Just == TEXT("Right")) TextBlock->SetJustification(ETextJustify::Right);
		}
	}

	// ProgressBar-specific
	if (UProgressBar* Bar = Cast<UProgressBar>(Widget))
	{
		if (Props->HasField(TEXT("percent")))
		{
			Bar->SetPercent(Props->GetNumberField(TEXT("percent")));
		}
		if (Props->HasField(TEXT("fill_color_r")) || Props->HasField(TEXT("fill_color_g")) || Props->HasField(TEXT("fill_color_b")))
		{
			float R = Props->HasField(TEXT("fill_color_r")) ? Props->GetNumberField(TEXT("fill_color_r")) : 1.0f;
			float G = Props->HasField(TEXT("fill_color_g")) ? Props->GetNumberField(TEXT("fill_color_g")) : 0.0f;
			float B = Props->HasField(TEXT("fill_color_b")) ? Props->GetNumberField(TEXT("fill_color_b")) : 0.0f;
			Bar->SetFillColorAndOpacity(FLinearColor(R, G, B, 1.0f));
		}
	}

	// Border-specific
	if (UBorder* Border = Cast<UBorder>(Widget))
	{
		if (Props->HasField(TEXT("background_r")) || Props->HasField(TEXT("background_g")) || Props->HasField(TEXT("background_b")))
		{
			float R = Props->HasField(TEXT("background_r")) ? Props->GetNumberField(TEXT("background_r")) : 0.0f;
			float G = Props->HasField(TEXT("background_g")) ? Props->GetNumberField(TEXT("background_g")) : 0.0f;
			float B = Props->HasField(TEXT("background_b")) ? Props->GetNumberField(TEXT("background_b")) : 0.0f;
			float A = Props->HasField(TEXT("background_a")) ? Props->GetNumberField(TEXT("background_a")) : 1.0f;
			Border->SetBrushColor(FLinearColor(R, G, B, A));
		}
		if (Props->HasField(TEXT("padding")))
		{
			float Pad = Props->GetNumberField(TEXT("padding"));
			Border->SetPadding(FMargin(Pad));
		}
	}

	// Image-specific
	if (UImage* Image = Cast<UImage>(Widget))
	{
		if (Props->HasField(TEXT("tint_r")) || Props->HasField(TEXT("tint_g")) || Props->HasField(TEXT("tint_b")))
		{
			float R = Props->HasField(TEXT("tint_r")) ? Props->GetNumberField(TEXT("tint_r")) : 1.0f;
			float G = Props->HasField(TEXT("tint_g")) ? Props->GetNumberField(TEXT("tint_g")) : 1.0f;
			float B = Props->HasField(TEXT("tint_b")) ? Props->GetNumberField(TEXT("tint_b")) : 1.0f;
			float A = Props->HasField(TEXT("tint_a")) ? Props->GetNumberField(TEXT("tint_a")) : 1.0f;
			Image->SetColorAndOpacity(FLinearColor(R, G, B, A));
		}
	}

	WidgetBP->MarkPackageDirty();
	FKismetEditorUtilities::CompileBlueprint(WidgetBP);

	TSharedPtr<FJsonObject> Result = MakeShareable(new FJsonObject);
	Result->SetBoolField(TEXT("success"), true);
	Result->SetStringField(TEXT("widget_name"), WidgetName);
	return Result;
}

// ============================================================================
// Helpers
// ============================================================================
UWidgetBlueprint* FEpicUnrealMCPWidgetCommands::FindWidgetBlueprint(const FString& Name)
{
	// Try common paths
	TArray<FString> SearchPaths = {
		FString::Printf(TEXT("/Game/SignalBound/UI/%s"), *Name),
		FString::Printf(TEXT("/Game/UI/%s"), *Name),
		FString::Printf(TEXT("/Game/Widgets/%s"), *Name),
		FString::Printf(TEXT("/Game/%s"), *Name)
	};

	for (const FString& Path : SearchPaths)
	{
		if (UEditorAssetLibrary::DoesAssetExist(Path))
		{
			UObject* Asset = UEditorAssetLibrary::LoadAsset(Path);
			if (UWidgetBlueprint* WBP = Cast<UWidgetBlueprint>(Asset))
			{
				return WBP;
			}
		}
	}

	// Try asset registry search by name
	FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
	TArray<FAssetData> AssetDataArray;
	AssetRegistryModule.Get().GetAssetsByClass(UWidgetBlueprint::StaticClass()->GetClassPathName(), AssetDataArray);

	for (const FAssetData& AssetData : AssetDataArray)
	{
		if (AssetData.AssetName.ToString() == Name)
		{
			return Cast<UWidgetBlueprint>(AssetData.GetAsset());
		}
	}

	return nullptr;
}

UWidget* FEpicUnrealMCPWidgetCommands::FindWidgetInTree(UWidgetBlueprint* WidgetBP, const FString& WidgetName)
{
	if (!WidgetBP || !WidgetBP->WidgetTree)
	{
		return nullptr;
	}

	UWidget* FoundWidget = nullptr;
	WidgetBP->WidgetTree->ForEachWidget([&](UWidget* Widget)
	{
		if (Widget && Widget->GetName() == WidgetName)
		{
			FoundWidget = Widget;
		}
	});

	return FoundWidget;
}
