#include "UI/SBWidget_SystemMenu.h"

USBWidget_SystemMenu::USBWidget_SystemMenu(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

void USBWidget_SystemMenu::NativeConstruct()
{
	Super::NativeConstruct();

	if (TabButton_Status)
	{
		TabButton_Status->OnClicked.AddDynamic(this, &USBWidget_SystemMenu::OnStatusClicked);
	}
	if (TabButton_Contracts)
	{
		TabButton_Contracts->OnClicked.AddDynamic(this, &USBWidget_SystemMenu::OnContractsClicked);
	}
	if (TabButton_Skills)
	{
		TabButton_Skills->OnClicked.AddDynamic(this, &USBWidget_SystemMenu::OnSkillsClicked);
	}

	SetVisibility(ESlateVisibility::Collapsed);
}

void USBWidget_SystemMenu::SelectTab(int32 TabIndex)
{
	CurrentTab = FMath::Clamp(TabIndex, 0, 2);

	if (TabSwitcher)
	{
		TabSwitcher->SetActiveWidgetIndex(CurrentTab);
	}

	OnTabChanged(CurrentTab);
}

void USBWidget_SystemMenu::OpenMenu()
{
	bIsOpen = true;
	SetVisibility(ESlateVisibility::Visible);
	SelectTab(CurrentTab);

	if (APlayerController* PC = GetOwningPlayer())
	{
		FInputModeGameAndUI InputMode;
		InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		PC->SetInputMode(InputMode);
		PC->SetShowMouseCursor(true);
	}

	OnMenuOpened();
}

void USBWidget_SystemMenu::CloseMenu()
{
	bIsOpen = false;
	SetVisibility(ESlateVisibility::Collapsed);

	if (APlayerController* PC = GetOwningPlayer())
	{
		FInputModeGameOnly InputMode;
		PC->SetInputMode(InputMode);
		PC->SetShowMouseCursor(false);
	}

	OnMenuClosed();
}

void USBWidget_SystemMenu::ToggleMenu()
{
	if (bIsOpen)
	{
		CloseMenu();
	}
	else
	{
		OpenMenu();
	}
}

void USBWidget_SystemMenu::OnStatusClicked()
{
	SelectTab(0);
}

void USBWidget_SystemMenu::OnContractsClicked()
{
	SelectTab(1);
}

void USBWidget_SystemMenu::OnSkillsClicked()
{
	SelectTab(2);
}
