#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

/**
 * Command handler for Widget Blueprint operations.
 * Supports creating widget blueprints, adding widgets to the tree,
 * setting slot properties, and configuring widget appearance.
 */
class FEpicUnrealMCPWidgetCommands
{
public:
	FEpicUnrealMCPWidgetCommands();

	TSharedPtr<FJsonObject> HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params);

private:
	// Create a new Widget Blueprint asset
	TSharedPtr<FJsonObject> HandleCreateWidgetBlueprint(const TSharedPtr<FJsonObject>& Params);

	// Add a widget (TextBlock, ProgressBar, Image, Button, etc.) to a Widget Blueprint's widget tree
	TSharedPtr<FJsonObject> HandleAddWidgetToCanvas(const TSharedPtr<FJsonObject>& Params);

	// Set slot properties (anchors, position, size) on a widget in the tree
	TSharedPtr<FJsonObject> HandleSetWidgetSlot(const TSharedPtr<FJsonObject>& Params);

	// Set appearance properties (color, font, opacity, text) on a widget
	TSharedPtr<FJsonObject> HandleSetWidgetAppearance(const TSharedPtr<FJsonObject>& Params);

	// Helper: find a WidgetBlueprint by name
	class UWidgetBlueprint* FindWidgetBlueprint(const FString& Name);

	// Helper: find a widget in the widget tree by name
	class UWidget* FindWidgetInTree(class UWidgetBlueprint* WidgetBP, const FString& WidgetName);
};
