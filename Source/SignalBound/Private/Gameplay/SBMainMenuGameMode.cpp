#include "Gameplay/SBMainMenuGameMode.h"

#include "UI/SBWidget_MainMenu.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/PlayerController.h"

ASBMainMenuGameMode::ASBMainMenuGameMode()
{
	PrimaryActorTick.bCanEverTick = false;
	DefaultPawnClass = nullptr;
}

void ASBMainMenuGameMode::BeginPlay()
{
	Super::BeginPlay();

	APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!PC)
	{
		return;
	}

	// Hide the default HUD
	PC->bShowMouseCursor = true;

	UClass* WidgetClass = MainMenuWidgetClass ? *MainMenuWidgetClass : nullptr;
	if (!WidgetClass)
	{
		// Fallback: try to load a Blueprint widget
		WidgetClass = LoadClass<USBWidget_MainMenu>(
			nullptr,
			TEXT("/Game/UI/WBP_MainMenu.WBP_MainMenu_C"));
	}

	if (WidgetClass)
	{
		MainMenuWidget = CreateWidget<USBWidget_MainMenu>(PC, WidgetClass);
		if (MainMenuWidget)
		{
			MainMenuWidget->AddToViewport(100);
			MainMenuWidget->ShowMenu();
		}
	}
}
