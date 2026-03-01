#include "UI/SBWidget_PlayerHUD.h"

USBWidget_PlayerHUD::USBWidget_PlayerHUD(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
}

void USBWidget_PlayerHUD::NativeConstruct()
{
	Super::NativeConstruct();

	if (HealthBar)
	{
		HealthBar->SetPercent(1.0f);
	}
	if (StaminaBar)
	{
		StaminaBar->SetPercent(1.0f);
	}
	if (CooldownArc)
	{
		CooldownArc->SetOpacity(0.0f);
	}
	if (ContractText)
	{
		ContractText->SetText(FText::GetEmpty());
	}
	if (DirectiveText)
	{
		DirectiveText->SetText(FText::GetEmpty());
	}
}

void USBWidget_PlayerHUD::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	CurrentHealth = FMath::FInterpTo(CurrentHealth, TargetHealth, InDeltaTime, InterpSpeed);
	CurrentStamina = FMath::FInterpTo(CurrentStamina, TargetStamina, InDeltaTime, InterpSpeed);
	CurrentCooldown = FMath::FInterpTo(CurrentCooldown, TargetCooldown, InDeltaTime, InterpSpeed);

	if (HealthBar)
	{
		HealthBar->SetPercent(CurrentHealth);
	}
	if (StaminaBar)
	{
		StaminaBar->SetPercent(CurrentStamina);
	}
	if (CooldownArc)
	{
		CooldownArc->SetOpacity(CurrentCooldown > 0.01f ? 1.0f : 0.0f);
	}
}

void USBWidget_PlayerHUD::UpdateHealth(float Percent)
{
	TargetHealth = FMath::Clamp(Percent, 0.0f, 1.0f);
}

void USBWidget_PlayerHUD::UpdateStamina(float Percent)
{
	TargetStamina = FMath::Clamp(Percent, 0.0f, 1.0f);
}

void USBWidget_PlayerHUD::UpdateCooldown(float Percent)
{
	TargetCooldown = FMath::Clamp(Percent, 0.0f, 1.0f);
}

void USBWidget_PlayerHUD::SetSkillReady(bool bReady)
{
	TargetCooldown = bReady ? 0.0f : 1.0f;
}

void USBWidget_PlayerHUD::UpdateContractText(const FString& InText)
{
	if (ContractText)
	{
		ContractText->SetText(FText::FromString(InText));
	}
}

void USBWidget_PlayerHUD::UpdateDirectiveText(const FString& InText)
{
	if (DirectiveText)
	{
		DirectiveText->SetText(FText::FromString(InText));
	}
}
