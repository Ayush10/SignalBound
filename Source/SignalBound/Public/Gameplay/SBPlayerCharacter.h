#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "SBPlayerCharacter.generated.h"

class UAnimMontage;
class UParticleSystem;
class USoundBase;
class ASBContractManager;
class ASBEnemyBase;
class USpringArmComponent;
class UCameraComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSBStatChangedSignature, float, NewNormalizedValue);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FSBPlayerSimpleSignature);

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBPlayerCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    ASBPlayerCharacter();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
    USpringArmComponent* CameraBoom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera")
    UCameraComponent* FollowCamera;

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

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

    UFUNCTION(BlueprintImplementableEvent, Category = "Combat")
    void ReceiveCombatNotify(FName NotifyName);

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
    float MeleeAttackRange = 150.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float MeleeAttackRadius = 85.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float HeavyAttackRangeBonus = 25.0f;

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

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float TurnRate = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat")
    float LookUpRate = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement")
    float MoveSpeedMultiplier = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Animation")
    UAnimMontage* LightAttackMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Animation")
    UAnimMontage* HeavyAttackMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Animation")
    UAnimMontage* DodgeMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Animation")
    UAnimMontage* BlockMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Animation")
    UAnimMontage* SkillMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Animation")
    UAnimMontage* DeathMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|VFX")
    UParticleSystem* CombatHitVFX = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|VFX")
    UParticleSystem* ParryVFX = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|SFX")
    USoundBase* CombatImpactSFX = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combat|Debug")
    bool bDebugCombatTrace = false;

private:
    void SetMoveForwardInput(float Value);
    void SetMoveRightInput(float Value);
    void ApplyMovementInput();
    void MoveForwardPressed();
    void MoveForwardReleased();
    void MoveBackwardPressed();
    void MoveBackwardReleased();
    void MoveRightPressed();
    void MoveRightReleased();
    void MoveLeftPressed();
    void MoveLeftReleased();
    void HandleLightAttackInput();
    void TurnAtRate(float Rate);
    void LookUpAtRate(float Rate);
    void TryHeavyAttackInput();
    void StopBlockInput();
    void TryDodgeInput();
    void TrySkillInput();
    void StartBlockInput();

    void ApplyAttackDamage(float DamageAmount, float AttackRange, float AttackRadius);
    void ApplySwordSkillDamage();
    void NotifyContractManagerOfHit(bool bSuccessfulParry = false);
    void NotifyContractManagerOfLowHealth();
    ASBContractManager* GetContractManager() const;

    void PlayMontageIfSet(UAnimMontage* MontageToPlay);
    void SpawnCombatFX(UParticleSystem* FX, const FVector& Location) const;
    void SpawnCombatSFX(const FVector& Location) const;
    void BroadcastNotify(FName NotifyName);

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
    float MoveForwardAxis = 0.0f;
    float MoveRightAxis = 0.0f;

    FTimerHandle AttackResetTimerHandle;
    FTimerHandle DodgeTimerHandle;
    FTimerHandle ParryTimerHandle;
};
