#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SBMainMenuGameMode.generated.h"

class USBWidget_MainMenu;

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBMainMenuGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ASBMainMenuGameMode();

	virtual void BeginPlay() override;

	UFUNCTION(BlueprintPure, Category = "MainMenu")
	USBWidget_MainMenu* GetMainMenuWidget() const { return MainMenuWidget; }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MainMenu")
	TSubclassOf<USBWidget_MainMenu> MainMenuWidgetClass;

private:
	UPROPERTY(Transient)
	USBWidget_MainMenu* MainMenuWidget = nullptr;
};
