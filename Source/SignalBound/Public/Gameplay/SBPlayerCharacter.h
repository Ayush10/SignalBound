#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SBPlayerCharacter.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSBStatChangedSignature, float, NewNormalizedValue);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FSBPlayerSimpleSignature);

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBPlayerCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    ASBPlayerCharacter();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Combat")
    void TakeDamageCustom(float DamageAmount);

    UFUNCTION(BlueprintCallable, Category = "Combat")
    bool TryLightAttack();

    UFUNCTION(BlueprintCallable, Category = "Combat")
    bool TryHeavyAttack();

    UFUNCTION(BlueprintCallable, Category = "Combat")
    bool TryDodge();

    UFUNCTION(BlueprintCallable, Category = "Combat")
    void StartBlock();

    UFUNCTION(BlueprintCallable, Category = "Combat")
    void StopBlock();

    UFUNCTION(BlueprintCallable, Category = "Combat")
    bool TrySwordSkill();

    UFUNCTION(BlueprintCallable, Category = "Combat")
    void OnParrySuccess();

    UFUNCTION(BlueprintCallable, Category = "Combat")
    void Die();

    UFUNCTION(BlueprintCallable, Category = "Combat")
    void UpdateStaminaRegen(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Combat")
    void UpdateSwordSkillCooldown(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Combat")
    void UpdateHUDValues();

    UFUNCTION(BlueprintCallable, Category = "Combat")
    void ResetAttackState();

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBStatChangedSignature OnHealthChanged;

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBStatChangedSignature OnStaminaChanged;

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBStatChangedSignature OnSwordCooldownChanged;

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBPlayerSimpleSignature OnPlayerDied;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stats")
    float MaxHealth = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stats")
    float CurrentHealth = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stats")
    float MaxStamina = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stats")
    float CurrentStamina = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stats")
    float StaminaRegenRate = 15.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stats")
    float StaminaRegenDelay = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float DodgeCost = 25.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float BlockDrainRate = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float LightAttackDamage = 15.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float HeavyAttackDamage = 35.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    int32 ComboIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    int32 MaxComboCount = 3;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float ComboResetTime = 1.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    bool bCanCombo = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    bool bIsAttacking = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    bool bIsBlocking = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    bool bIsDodging = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    bool bParryWindowActive = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float ParryWindowDuration = 0.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float SwordSkillCooldown = 8.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float SwordSkillCooldownRemaining = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    bool bSwordSkillReady = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    bool bIsDead = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    bool bIsInvincible = false;

private:
    bool ConsumeStamina(float Amount);
    void MarkStaminaSpent();

    UFUNCTION()
    void EndDodge();

    UFUNCTION()
    void DisableParryWindow();

    float TimeSinceLastStaminaSpend = 0.0f;
    float LastHealthPct = 1.0f;
    float LastStaminaPct = 1.0f;
    float LastCooldownPct = 0.0f;

    FTimerHandle AttackResetTimerHandle;
    FTimerHandle DodgeTimerHandle;
    FTimerHandle ParryTimerHandle;
};
