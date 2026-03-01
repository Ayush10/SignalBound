#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/TextBlock.h"
#include "Components/Border.h"
#include "SBWidget_SystemNotice.generated.h"

UCLASS(Abstract)
class SIGNALBOUND_API USBWidget_SystemNotice : public UUserWidget
{
	GENERATED_BODY()

public:
	USBWidget_SystemNotice(const FObjectInitializer& ObjectInitializer);

	UFUNCTION(BlueprintCallable, Category = "Notice")
	void ShowNotice(const FString& Text, float Duration = 3.0f);

	UFUNCTION(BlueprintCallable, Category = "Notice")
	void HideNotice();

	UFUNCTION(BlueprintCallable, Category = "Notice")
	bool IsNoticeVisible() const { return bIsShowing; }

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UTextBlock* NoticeText;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UBorder* NoticePanel;

	UFUNCTION(BlueprintImplementableEvent, Category = "Notice")
	void OnNoticeShown();

	UFUNCTION(BlueprintImplementableEvent, Category = "Notice")
	void OnNoticeHidden();

private:
	bool bIsShowing = false;
	float DisplayTimer = 0.0f;
	float DisplayDuration = 3.0f;
	float CurrentOpacity = 0.0f;
	float FadeSpeed = 5.0f;
};
