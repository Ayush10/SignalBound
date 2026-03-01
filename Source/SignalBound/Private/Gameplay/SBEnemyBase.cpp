#include "Gameplay/SBEnemyBase.h"

#include "AIController.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Gameplay/SBPlayerCharacter.h"
#include "Kismet/GameplayStatics.h"
#include "Animation/AnimInstance.h"

ASBEnemyBase::ASBEnemyBase()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ASBEnemyBase::BeginPlay()
{
    Super::BeginPlay();

    MaxHealth = FMath::Max(1.0f, MaxHealth);
    CurrentHealth = FMath::Clamp(CurrentHealth, 0.0f, MaxHealth);
    EnterState(static_cast<int32>(ESBEnemyState::Idle));
}

void ASBEnemyBase::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    TickStateMachine(DeltaSeconds);
}

void ASBEnemyBase::ReceiveDamage(float DamageAmount)
{
    if (bIsDead || DamageAmount <= 0.0f)
    {
        return;
    }

    CurrentHealth = FMath::Clamp(CurrentHealth - DamageAmount, 0.0f, MaxHealth);
    AccumulatedStagger += DamageAmount;
    SpawnEnemyFX(HitFX, GetActorLocation() + FVector(0.0f, 0.0f, 60.0f));
    SpawnEnemySFX(GetActorLocation());

    if (CurrentHealth <= 0.0f)
    {
        Die();
        return;
    }

    if (AccumulatedStagger >= StaggerThreshold)
    {
        AccumulatedStagger = 0.0f;
        EnterState(static_cast<int32>(ESBEnemyState::Stunned));
        return;
    }

    EnterState(static_cast<int32>(ESBEnemyState::HitReact));
}

void ASBEnemyBase::EnterState(int32 NewStateIndex)
{
    CurrentStateIndex = FMath::Clamp(NewStateIndex, 0, static_cast<int32>(ESBEnemyState::Dead));
    StateElapsed = 0.0f;
    bAttackExecuted = false;

    switch (static_cast<ESBEnemyState>(CurrentStateIndex))
    {
    case ESBEnemyState::Idle:
        StateDuration = 0.0f;
        ReceiveCombatNotify(TEXT("Idle"));
        break;
    case ESBEnemyState::Chase:
        StateDuration = 0.0f;
        ReceiveCombatNotify(TEXT("Chase"));
        break;
    case ESBEnemyState::Windup:
        StateDuration = FMath::Max(0.05f, WindupDuration);
        PlayMontageIfSet(WindupMontage);
        ReceiveCombatNotify(TEXT("Windup"));
        break;
    case ESBEnemyState::Attack:
        StateDuration = 0.2f;
        PlayMontageIfSet(AttackMontage);
        SpawnEnemyFX(HitFX, GetActorLocation() + FVector(0.0f, 0.0f, 60.0f));
        SpawnEnemySFX(GetActorLocation());
        ReceiveCombatNotify(TEXT("Attack"));
        break;
    case ESBEnemyState::Recover:
        StateDuration = FMath::Max(0.05f, RecoveryDuration);
        ReceiveCombatNotify(TEXT("Recover"));
        break;
    case ESBEnemyState::Stunned:
        StateDuration = 0.9f;
        PlayMontageIfSet(StunMontage);
        ReceiveCombatNotify(TEXT("Stunned"));
        break;
    case ESBEnemyState::HitReact:
        StateDuration = 0.35f;
        PlayMontageIfSet(HitReactMontage);
        ReceiveCombatNotify(TEXT("HitReact"));
        break;
    case ESBEnemyState::Dead:
        StateDuration = 0.0f;
        PlayMontageIfSet(DeathMontage);
        SpawnEnemyFX(DeathFX, GetActorLocation());
        ReceiveCombatNotify(TEXT("Death"));
        break;
    default:
        StateDuration = 0.0f;
        break;
    }
}

void ASBEnemyBase::TickStateMachine(float DeltaSeconds)
{
    if (bIsDead)
    {
        return;
    }

    StateElapsed += DeltaSeconds;
    switch (static_cast<ESBEnemyState>(CurrentStateIndex))
    {
    case ESBEnemyState::Idle:
        TickIdle(DeltaSeconds);
        break;
    case ESBEnemyState::Chase:
        TickChase(DeltaSeconds);
        break;
    case ESBEnemyState::Windup:
        TickWindup(DeltaSeconds);
        break;
    case ESBEnemyState::Attack:
        TickAttack(DeltaSeconds);
        break;
    case ESBEnemyState::Recover:
        TickRecover(DeltaSeconds);
        break;
    case ESBEnemyState::Stunned:
        TickStunned(DeltaSeconds);
        break;
    case ESBEnemyState::HitReact:
        TickHitReact(DeltaSeconds);
        break;
    case ESBEnemyState::Dead:
        break;
    default:
        break;
    }
}

void ASBEnemyBase::TickIdle(float DeltaSeconds)
{
    if (DeltaSeconds < 0.0f)
    {
        return;
    }

    TargetActor = AcquireTarget();
    if (TargetActor)
    {
        EnterState(static_cast<int32>(ESBEnemyState::Chase));
    }
}

void ASBEnemyBase::TickChase(float DeltaSeconds)
{
    if (DeltaSeconds < 0.0f)
    {
        return;
    }

    if (!TargetActor)
    {
        TargetActor = AcquireTarget();
        if (!TargetActor)
        {
            EnterState(static_cast<int32>(ESBEnemyState::Idle));
            return;
        }
    }

    const FVector ToTarget = TargetActor->GetActorLocation() - GetActorLocation();
    const float Distance = ToTarget.Size();

    if (Distance > DetectionRange * 1.4f)
    {
        TargetActor = nullptr;
        EnterState(static_cast<int32>(ESBEnemyState::Idle));
        return;
    }

    if (Distance <= AttackRange)
    {
        EnterState(static_cast<int32>(ESBEnemyState::Windup));
        return;
    }

    if (UCharacterMovementComponent* MoveComp = GetCharacterMovement())
    {
        MoveComp->MaxWalkSpeed = ChaseSpeed;
    }

    if (AAIController* AIController = Cast<AAIController>(GetController()))
    {
        AIController->MoveToActor(TargetActor, FMath::Max(80.0f, AttackRange * 0.75f));
    }
    else
    {
        const FVector Direction = ToTarget.GetSafeNormal2D();
        AddMovementInput(Direction, 1.0f);
    }
}

void ASBEnemyBase::TickWindup(float DeltaSeconds)
{
    if (DeltaSeconds < 0.0f)
    {
        return;
    }

    if (StateElapsed >= StateDuration)
    {
        EnterState(static_cast<int32>(ESBEnemyState::Attack));
    }
}

void ASBEnemyBase::TickAttack(float DeltaSeconds)
{
    if (DeltaSeconds < 0.0f)
    {
        return;
    }

    if (!bAttackExecuted)
    {
        PerformAttack();
        bAttackExecuted = true;
    }

    if (StateElapsed >= StateDuration)
    {
        EnterState(static_cast<int32>(ESBEnemyState::Recover));
    }
}

void ASBEnemyBase::TickRecover(float DeltaSeconds)
{
    if (DeltaSeconds < 0.0f)
    {
        return;
    }

    if (StateElapsed >= StateDuration)
    {
        if (TargetActor)
        {
            EnterState(static_cast<int32>(ESBEnemyState::Chase));
        }
        else
        {
            EnterState(static_cast<int32>(ESBEnemyState::Idle));
        }
    }
}

void ASBEnemyBase::TickStunned(float DeltaSeconds)
{
    if (DeltaSeconds < 0.0f)
    {
        return;
    }

    if (StateElapsed >= StateDuration)
    {
        EnterState(static_cast<int32>(ESBEnemyState::Chase));
    }
}

void ASBEnemyBase::TickHitReact(float DeltaSeconds)
{
    if (DeltaSeconds < 0.0f)
    {
        return;
    }

    if (StateElapsed >= StateDuration)
    {
        EnterState(static_cast<int32>(ESBEnemyState::Chase));
    }
}

void ASBEnemyBase::Die()
{
    if (bIsDead)
    {
        return;
    }

    bIsDead = true;
    EnterState(static_cast<int32>(ESBEnemyState::Dead));

    if (AAIController* AIController = Cast<AAIController>(GetController()))
    {
        AIController->StopMovement();
    }

    if (UCharacterMovementComponent* MoveComp = GetCharacterMovement())
    {
        MoveComp->DisableMovement();
    }

    OnEnemyDied.Broadcast(this);
}

void ASBEnemyBase::PerformAttack()
{
    if (!TargetActor || bIsDead)
    {
        return;
    }

    const float Distance = FVector::Dist(TargetActor->GetActorLocation(), GetActorLocation());
    if (Distance > AttackRange * 1.25f)
    {
        return;
    }

    if (ASBPlayerCharacter* Player = Cast<ASBPlayerCharacter>(TargetActor))
    {
        Player->TakeDamageCustom(AttackDamage);
    }
}

AActor* ASBEnemyBase::AcquireTarget() const
{
    APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
    if (!PlayerPawn)
    {
        return nullptr;
    }

    const float Distance = FVector::Dist(PlayerPawn->GetActorLocation(), GetActorLocation());
    return Distance <= DetectionRange ? PlayerPawn : nullptr;
}

void ASBEnemyBase::PlayMontageIfSet(UAnimMontage* MontageToPlay) const
{
    if (!MontageToPlay)
    {
        return;
    }

    if (USkeletalMeshComponent* MeshComp = GetMesh())
    {
        if (UAnimInstance* AnimInstance = MeshComp->GetAnimInstance())
        {
            AnimInstance->Montage_Play(MontageToPlay, 1.0f);
        }
    }
}

void ASBEnemyBase::SpawnEnemyFX(UParticleSystem* FX, const FVector& Location) const
{
    if (!FX || !GetWorld())
    {
        return;
    }

    UGameplayStatics::SpawnEmitterAtLocation(GetWorld(), FX, Location, FRotator::ZeroRotator, true);
}

void ASBEnemyBase::SpawnEnemySFX(const FVector& Location) const
{
    if (!AttackSFX || !GetWorld())
    {
        return;
    }

    UGameplayStatics::PlaySoundAtLocation(this, AttackSFX, Location);
}
