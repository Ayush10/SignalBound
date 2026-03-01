#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/ProgressBar.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "SBWidget_PlayerHUD.generated.h"

UCLASS(Abstract)
class SIGNALBOUND_API USBWidget_PlayerHUD : public UUserWidget
{
	GENERATED_BODY()

public:
	USBWidget_PlayerHUD(const FObjectInitializer& ObjectInitializer);

	UFUNCTION(BlueprintCallable, Category = "HUD")
	void UpdateHealth(float Percent);

	UFUNCTION(BlueprintCallable, Category = "HUD")
	void UpdateStamina(float Percent);

	UFUNCTION(BlueprintCallable, Category = "HUD")
	void UpdateCooldown(float Percent);

	UFUNCTION(BlueprintCallable, Category = "HUD")
	void SetSkillReady(bool bReady);

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UProgressBar* HealthBar;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UProgressBar* StaminaBar;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UImage* CooldownArc;

	UPROPERTY(BlueprintReadOnly, meta = (BindWidget))
	UTextBlock* ContractText;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
	float InterpSpeed = 10.0f;

private:
	float TargetHealth = 1.0f;
	float TargetStamina = 1.0f;
	float TargetCooldown = 0.0f;
	float CurrentHealth = 1.0f;
	float CurrentStamina = 1.0f;
	float CurrentCooldown = 0.0f;
};
