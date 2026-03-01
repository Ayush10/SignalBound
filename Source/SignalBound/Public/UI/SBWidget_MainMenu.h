#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "Components/Slider.h"
#include "Components/TextBlock.h"
#include "Components/Image.h"
#include "SBWidget_MainMenu.generated.h"

UCLASS(Abstract)
class SIGNALBOUND_API USBWidget_MainMenu : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "MainMenu")
	void ShowMenu();

	UFUNCTION(BlueprintCallable, Category = "MainMenu")
	void HideMenu();

	UFUNCTION(BlueprintCallable, Category = "MainMenu")
	bool HasSaveGame() const;

protected:
	virtual void NativeConstruct() override;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UButton* Btn_StartGame;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UButton* Btn_ResumeGame;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UButton* Btn_ExitGame;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UButton* Btn_ToggleSound;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	USlider* Slider_Volume;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional))
	UTextBlock* Text_VolumeLabel;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional))
	UTextBlock* Text_SoundStatus;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidgetOptional))
	UTextBlock* Text_Title;

	UFUNCTION(BlueprintImplementableEvent, Category = "MainMenu")
	void OnGameStarted();

	UFUNCTION(BlueprintImplementableEvent, Category = "MainMenu")
	void OnGameResumed();

private:
	UFUNCTION()
	void HandleStartGame();

	UFUNCTION()
	void HandleResumeGame();

	UFUNCTION()
	void HandleExitGame();

	UFUNCTION()
	void HandleToggleSound();

	UFUNCTION()
	void HandleVolumeChanged(float Value);

	bool bSoundEnabled = true;
	float CurrentVolume = 1.0f;
};
