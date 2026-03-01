#include "UI/SBWidget_SystemNotice.h"

USBWidget_SystemNotice::USBWidget_SystemNotice(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

void USBWidget_SystemNotice::NativeConstruct()
{
	Super::NativeConstruct();

	if (NoticePanel)
	{
		NoticePanel->SetRenderOpacity(0.0f);
	}
}

void USBWidget_SystemNotice::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	float TargetOpacity = bIsShowing ? 1.0f : 0.0f;
	CurrentOpacity = FMath::FInterpTo(CurrentOpacity, TargetOpacity, InDeltaTime, FadeSpeed);

	if (NoticePanel)
	{
		NoticePanel->SetRenderOpacity(CurrentOpacity);
	}

	if (bIsShowing)
	{
		DisplayTimer += InDeltaTime;
		if (DisplayTimer >= DisplayDuration)
		{
			HideNotice();
		}
	}
}

void USBWidget_SystemNotice::ShowNotice(const FString& Text, float Duration)
{
	if (NoticeText)
	{
		NoticeText->SetText(FText::FromString(Text));
	}

	DisplayDuration = Duration;
	DisplayTimer = 0.0f;
	bIsShowing = true;

	OnNoticeShown();
}

void USBWidget_SystemNotice::HideNotice()
{
	bIsShowing = false;
	DisplayTimer = 0.0f;

	OnNoticeHidden();
}
