#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "Gameplay/SBGameplayTypes.h"
#include "SBEnemyBase.generated.h"

class ASBEnemyBase;
class UAnimMontage;
class UParticleSystem;
class USoundBase;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSBEnemyDiedSignature, ASBEnemyBase*, Enemy);

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBEnemyBase : public ACharacter
{
    GENERATED_BODY()

public:
    ASBEnemyBase();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void ReceiveDamage(float DamageAmount);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void EnterState(int32 NewStateIndex);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void TickStateMachine(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void TickIdle(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void TickChase(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void TickWindup(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void TickAttack(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void TickRecover(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void TickStunned(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void TickHitReact(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Enemy")
    void Die();

    UFUNCTION(BlueprintPure, Category = "Enemy")
    ESBEnemyState GetCurrentState() const
    {
        return static_cast<ESBEnemyState>(CurrentStateIndex);
    }

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBEnemyDiedSignature OnEnemyDied;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float MaxHealth = 80.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float CurrentHealth = 80.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float AttackDamage = 12.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float DetectionRange = 1000.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float AttackRange = 180.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float ChaseSpeed = 320.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float WindupDuration = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float RecoveryDuration = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    float StaggerThreshold = 25.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Config")
    bool bIsRanged = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Runtime")
    float AccumulatedStagger = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Runtime")
    int32 CurrentStateIndex = static_cast<int32>(ESBEnemyState::Idle);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Runtime")
    bool bIsDead = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Runtime")
    AActor* TargetActor = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    UAnimMontage* WindupMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    UAnimMontage* AttackMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    UAnimMontage* HitReactMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    UAnimMontage* StunMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Animation")
    UAnimMontage* DeathMontage = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VFX")
    UParticleSystem* HitFX = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VFX")
    UParticleSystem* DeathFX = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SFX")
    USoundBase* AttackSFX = nullptr;

protected:
    UFUNCTION(BlueprintCallable, Category = "Enemy")
    virtual void PerformAttack();

    UFUNCTION(BlueprintImplementableEvent, Category = "Enemy")
    void ReceiveCombatNotify(FName NotifyName);

private:
    AActor* AcquireTarget() const;
    void PlayMontageIfSet(UAnimMontage* MontageToPlay) const;
    void SpawnEnemyFX(UParticleSystem* FX, const FVector& Location) const;
    void SpawnEnemySFX(const FVector& Location) const;
    float StateElapsed = 0.0f;
    float StateDuration = 0.0f;
    bool bAttackExecuted = false;
};
