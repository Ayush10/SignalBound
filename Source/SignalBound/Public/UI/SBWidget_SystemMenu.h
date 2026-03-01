#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/WidgetSwitcher.h"
#include "Components/Button.h"
#include "Components/Border.h"
#include "SBWidget_SystemMenu.generated.h"

UCLASS(Abstract)
class SIGNALBOUND_API USBWidget_SystemMenu : public UUserWidget
{
	GENERATED_BODY()

public:
	USBWidget_SystemMenu(const FObjectInitializer& ObjectInitializer);

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void SelectTab(int32 TabIndex);

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void OpenMenu();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void CloseMenu();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	void ToggleMenu();

	UFUNCTION(BlueprintCallable, Category = "Menu")
	bool IsMenuOpen() const { return bIsOpen; }

	UFUNCTION(BlueprintCallable, Category = "Menu")
	int32 GetCurrentTab() const { return CurrentTab; }

protected:
	virtual void NativeConstruct() override;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UWidgetSwitcher* TabSwitcher;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UButton* TabButton_Status;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UButton* TabButton_Contracts;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UButton* TabButton_Skills;

	UFUNCTION(BlueprintImplementableEvent, Category = "Menu")
	void OnMenuOpened();

	UFUNCTION(BlueprintImplementableEvent, Category = "Menu")
	void OnMenuClosed();

	UFUNCTION(BlueprintImplementableEvent, Category = "Menu")
	void OnTabChanged(int32 NewTab);

private:
	UFUNCTION()
	void OnStatusClicked();

	UFUNCTION()
	void OnContractsClicked();

	UFUNCTION()
	void OnSkillsClicked();

	int32 CurrentTab = 0;
	bool bIsOpen = false;
};
