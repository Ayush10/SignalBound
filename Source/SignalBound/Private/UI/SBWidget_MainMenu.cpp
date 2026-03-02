#include "UI/SBWidget_MainMenu.h"

#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "GameFramework/PlayerController.h"
#include "AudioDevice.h"

void USBWidget_MainMenu::NativeConstruct()
{
	Super::NativeConstruct();

	if (Btn_StartGame)
	{
		Btn_StartGame->OnClicked.AddDynamic(this, &USBWidget_MainMenu::HandleStartGame);
	}
	if (Btn_ResumeGame)
	{
		Btn_ResumeGame->OnClicked.AddDynamic(this, &USBWidget_MainMenu::HandleResumeGame);
		Btn_ResumeGame->SetIsEnabled(HasSaveGame());
	}
	if (Btn_ExitGame)
	{
		Btn_ExitGame->OnClicked.AddDynamic(this, &USBWidget_MainMenu::HandleExitGame);
	}
	if (Btn_ToggleSound)
	{
		Btn_ToggleSound->OnClicked.AddDynamic(this, &USBWidget_MainMenu::HandleToggleSound);
	}
	if (Slider_Volume)
	{
		Slider_Volume->SetMinValue(0.0f);
		Slider_Volume->SetMaxValue(1.0f);
		Slider_Volume->SetValue(1.0f);
		Slider_Volume->OnValueChanged.AddDynamic(this, &USBWidget_MainMenu::HandleVolumeChanged);
	}

	if (Text_Title)
	{
		Text_Title->SetText(FText::FromString(TEXT("SIGNALBOUND")));
	}
	if (Text_SoundStatus)
	{
		Text_SoundStatus->SetText(FText::FromString(TEXT("Sound: ON")));
	}
	if (Text_VolumeLabel)
	{
		Text_VolumeLabel->SetText(FText::FromString(TEXT("Volume: 100%")));
	}
}

void USBWidget_MainMenu::ShowMenu()
{
	SetVisibility(ESlateVisibility::Visible);

	if (APlayerController* PC = GetOwningPlayer())
	{
		FInputModeUIOnly InputMode;
		InputMode.SetWidgetToFocus(TakeWidget());
		InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		PC->SetInputMode(InputMode);
		PC->bShowMouseCursor = true;
	}

	if (Btn_ResumeGame)
	{
		Btn_ResumeGame->SetIsEnabled(HasSaveGame());
	}
}

void USBWidget_MainMenu::HideMenu()
{
	SetVisibility(ESlateVisibility::Collapsed);

	if (APlayerController* PC = GetOwningPlayer())
	{
		FInputModeGameOnly InputMode;
		PC->SetInputMode(InputMode);
		PC->bShowMouseCursor = false;
	}
}

bool USBWidget_MainMenu::HasSaveGame() const
{
	return UGameplayStatics::DoesSaveGameExist(TEXT("SignalBound_Save"), 0);
}

void USBWidget_MainMenu::HandleStartGame()
{
	HideMenu();
	UGameplayStatics::OpenLevel(this, FName(TEXT("Map_HubCitadelCity")));
	OnGameStarted();
}

void USBWidget_MainMenu::HandleResumeGame()
{
	if (!HasSaveGame())
	{
		return;
	}
	HideMenu();
	UGameplayStatics::OpenLevel(this, FName(TEXT("Map_HubCitadelCity")));
	OnGameResumed();
}

void USBWidget_MainMenu::HandleExitGame()
{
	if (APlayerController* PC = GetOwningPlayer())
	{
		UKismetSystemLibrary::QuitGame(this, PC, EQuitPreference::Quit, false);
	}
}

void USBWidget_MainMenu::HandleToggleSound()
{
	bSoundEnabled = !bSoundEnabled;

	const float TargetVolume = bSoundEnabled ? CurrentVolume : 0.0f;
	if (GEngine)
	{
		FAudioDeviceHandle AudioDevice = GEngine->GetActiveAudioDevice();
		if (AudioDevice.IsValid())
		{
			AudioDevice.GetAudioDevice()->SetTransientPrimaryVolume(TargetVolume);
		}
	}

	if (Text_SoundStatus)
	{
		Text_SoundStatus->SetText(FText::FromString(
			bSoundEnabled ? TEXT("Sound: ON") : TEXT("Sound: OFF")));
	}

	if (Slider_Volume)
	{
		Slider_Volume->SetIsEnabled(bSoundEnabled);
	}
}

void USBWidget_MainMenu::HandleVolumeChanged(float Value)
{
	CurrentVolume = FMath::Clamp(Value, 0.0f, 1.0f);

	if (bSoundEnabled && GEngine)
	{
		FAudioDeviceHandle AudioDevice = GEngine->GetActiveAudioDevice();
		if (AudioDevice.IsValid())
		{
			AudioDevice.GetAudioDevice()->SetTransientPrimaryVolume(CurrentVolume);
		}
	}

	if (Text_VolumeLabel)
	{
		int32 Percent = FMath::RoundToInt(CurrentVolume * 100.0f);
		Text_VolumeLabel->SetText(FText::FromString(FString::Printf(TEXT("Volume: %d%%"), Percent)));
	}
}
