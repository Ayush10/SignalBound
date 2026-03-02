#include "Gameplay/SBPlayerCharacter.h"

#include "Components/InputComponent.h"
#include "EngineUtils.h"
#include "DrawDebugHelpers.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/CameraComponent.h"
#include "Gameplay/SBContractManager.h"
#include "Gameplay/SBEnemyBase.h"
#include "TimerManager.h"
#include "Kismet/GameplayStatics.h"
#include "Animation/AnimInstance.h"

ASBPlayerCharacter::ASBPlayerCharacter()
{
    PrimaryActorTick.bCanEverTick = true;

    // Camera setup
    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength = 400.0f; 
    CameraBoom->SocketOffset = FVector(0.0f, 0.0f, 60.0f);
    CameraBoom->bUsePawnControlRotation = true;

    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    FollowCamera->bUsePawnControlRotation = false;

    // Standard character rotation
    bUseControllerRotationPitch = false;
    bUseControllerRotationYaw = false;
    bUseControllerRotationRoll = false;

    if (UCharacterMovementComponent* MoveComp = GetCharacterMovement())
    {
        MoveComp->bOrientRotationToMovement = true; 
        MoveComp->RotationRate = FRotator(0.0f, 540.0f, 0.0f);
    }
}

void ASBPlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    if (!PlayerInputComponent)
    {
        return;
    }

    // Input mapping axis bindings (if action/axis mappings exist in Project Settings).
    PlayerInputComponent->BindAxis("MoveForward", this, &ASBPlayerCharacter::SetMoveForwardInput);
    PlayerInputComponent->BindAxis("MoveRight", this, &ASBPlayerCharacter::SetMoveRightInput);
    PlayerInputComponent->BindAxis("Turn", this, &ASBPlayerCharacter::TurnAtRate);
    PlayerInputComponent->BindAxis("LookUp", this, &ASBPlayerCharacter::LookUpAtRate);

    // WASD Movement
    PlayerInputComponent->BindKey(EKeys::W, IE_Pressed, this, &ASBPlayerCharacter::MoveForwardPressed);
    PlayerInputComponent->BindKey(EKeys::W, IE_Released, this, &ASBPlayerCharacter::MoveForwardReleased);
    PlayerInputComponent->BindKey(EKeys::S, IE_Pressed, this, &ASBPlayerCharacter::MoveBackwardPressed);
    PlayerInputComponent->BindKey(EKeys::S, IE_Released, this, &ASBPlayerCharacter::MoveBackwardReleased);
    PlayerInputComponent->BindKey(EKeys::D, IE_Pressed, this, &ASBPlayerCharacter::MoveRightPressed);
    PlayerInputComponent->BindKey(EKeys::D, IE_Released, this, &ASBPlayerCharacter::MoveRightReleased);
    PlayerInputComponent->BindKey(EKeys::A, IE_Pressed, this, &ASBPlayerCharacter::MoveLeftPressed);
    PlayerInputComponent->BindKey(EKeys::A, IE_Released, this, &ASBPlayerCharacter::MoveLeftReleased);

    // Arrow Key Movement
    PlayerInputComponent->BindKey(EKeys::Up, IE_Pressed, this, &ASBPlayerCharacter::MoveForwardPressed);
    PlayerInputComponent->BindKey(EKeys::Up, IE_Released, this, &ASBPlayerCharacter::MoveForwardReleased);
    PlayerInputComponent->BindKey(EKeys::Down, IE_Pressed, this, &ASBPlayerCharacter::MoveBackwardPressed);
    PlayerInputComponent->BindKey(EKeys::Down, IE_Released, this, &ASBPlayerCharacter::MoveBackwardReleased);
    PlayerInputComponent->BindKey(EKeys::Right, IE_Pressed, this, &ASBPlayerCharacter::MoveRightPressed);
    PlayerInputComponent->BindKey(EKeys::Right, IE_Released, this, &ASBPlayerCharacter::MoveRightReleased);
    PlayerInputComponent->BindKey(EKeys::Left, IE_Pressed, this, &ASBPlayerCharacter::MoveLeftPressed);
    PlayerInputComponent->BindKey(EKeys::Left, IE_Released, this, &ASBPlayerCharacter::MoveLeftReleased);

    PlayerInputComponent->BindAction("Jump", IE_Pressed, this, &ASBPlayerCharacter::Jump);
    PlayerInputComponent->BindAction("Jump", IE_Released, this, &ASBPlayerCharacter::StopJumping);

    PlayerInputComponent->BindKey(EKeys::LeftMouseButton, IE_Pressed, this, &ASBPlayerCharacter::HandleLightAttackInput);
    PlayerInputComponent->BindKey(EKeys::RightMouseButton, IE_Pressed, this, &ASBPlayerCharacter::TryHeavyAttackInput);
    PlayerInputComponent->BindKey(EKeys::LeftShift, IE_Pressed, this, &ASBPlayerCharacter::StartBlockInput);
    PlayerInputComponent->BindKey(EKeys::LeftShift, IE_Released, this, &ASBPlayerCharacter::StopBlockInput);
    PlayerInputComponent->BindKey(EKeys::SpaceBar, IE_Pressed, this, &ASBPlayerCharacter::TryDodgeInput);
    PlayerInputComponent->BindKey(EKeys::Q, IE_Pressed, this, &ASBPlayerCharacter::TrySkillInput);
}

void ASBPlayerCharacter::BeginPlay()
{
    Super::BeginPlay();

    if (APlayerController* PC = Cast<APlayerController>(GetController()))
    {
        FInputModeGameOnly InputMode;
        PC->SetInputMode(InputMode);
        PC->bShowMouseCursor = false;
    }

    MaxHealth = FMath::Max(1.0f, MaxHealth);
    MaxStamina = FMath::Max(1.0f, MaxStamina);
    CurrentHealth = FMath::Clamp(CurrentHealth, 0.0f, MaxHealth);
    CurrentStamina = FMath::Clamp(CurrentStamina, 0.0f, MaxStamina);
    SwordSkillCooldownRemaining = FMath::Max(0.0f, SwordSkillCooldownRemaining);
    bSwordSkillReady = SwordSkillCooldownRemaining <= 0.0f;

    LastHealthPct = CurrentHealth / MaxHealth;
    LastStaminaPct = CurrentStamina / MaxStamina;
    LastCooldownPct = SwordSkillCooldown > 0.0f
        ? (SwordSkillCooldownRemaining / SwordSkillCooldown)
        : 0.0f;

    UpdateHUDValues();
}

void ASBPlayerCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    if (bIsDead)
    {
        return;
    }

    TimeSinceLastStaminaSpend += DeltaSeconds;
    ApplyMovementInput();
    UpdateStaminaRegen(DeltaSeconds);
    UpdateSwordSkillCooldown(DeltaSeconds);
    UpdateHUDValues();
    NotifyContractManagerOfLowHealth();
}

void ASBPlayerCharacter::SetMoveForwardInput(float Value)
{
    if (bIsDead)
    {
        return;
    }
    MoveForwardAxis = FMath::Clamp(Value, -1.0f, 1.0f);
}

void ASBPlayerCharacter::SetMoveRightInput(float Value)
{
    if (bIsDead)
    {
        return;
    }
    MoveRightAxis = FMath::Clamp(Value, -1.0f, 1.0f);
}

void ASBPlayerCharacter::ApplyMovementInput()
{
    if (bIsDead || !Controller)
    {
        return;
    }

    const bool bHasInput = !FMath::IsNearlyZero(MoveForwardAxis) || !FMath::IsNearlyZero(MoveRightAxis);
    if (!bHasInput)
    {
        return;
    }

    const FRotator Rotation = Controller->GetControlRotation();
    const FRotator YawRotation(0.0f, Rotation.Yaw, 0.0f);

    if (!FMath::IsNearlyZero(MoveForwardAxis))
    {
        const FVector Direction = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
        AddMovementInput(Direction, MoveForwardAxis * MoveSpeedMultiplier);
    }

    if (!FMath::IsNearlyZero(MoveRightAxis))
    {
        const FVector Direction = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y);
        AddMovementInput(Direction, MoveRightAxis * MoveSpeedMultiplier);
    }
}

void ASBPlayerCharacter::MoveForwardPressed()
{
    if (bIsDead)
    {
        return;
    }
    MoveForwardAxis = 1.0f;
}

void ASBPlayerCharacter::MoveForwardReleased()
{
    if (!bIsDead && MoveForwardAxis > 0.0f) MoveForwardAxis = 0.0f;
}

void ASBPlayerCharacter::MoveBackwardPressed()
{
    if (bIsDead)
    {
        return;
    }
    MoveForwardAxis = -1.0f;
}

void ASBPlayerCharacter::MoveBackwardReleased()
{
    if (!bIsDead && MoveForwardAxis < 0.0f) MoveForwardAxis = 0.0f;
}

void ASBPlayerCharacter::MoveRightPressed()
{
    if (bIsDead)
    {
        return;
    }
    MoveRightAxis = 1.0f;
}

void ASBPlayerCharacter::MoveRightReleased()
{
    if (!bIsDead && MoveRightAxis > 0.0f) MoveRightAxis = 0.0f;
}

void ASBPlayerCharacter::MoveLeftPressed()
{
    if (bIsDead)
    {
        return;
    }
    MoveRightAxis = -1.0f;
}

void ASBPlayerCharacter::MoveLeftReleased()
{
    if (!bIsDead && MoveRightAxis < 0.0f) MoveRightAxis = 0.0f;
}

void ASBPlayerCharacter::HandleLightAttackInput()
{
    TryLightAttack();
}

void ASBPlayerCharacter::TurnAtRate(float Rate)
{
    if (bIsDead)
    {
        return;
    }
    AddControllerYawInput(Rate * TurnRate);
}

void ASBPlayerCharacter::LookUpAtRate(float Rate)
{
    if (bIsDead)
    {
        return;
    }
    AddControllerPitchInput(Rate * LookUpRate);
}

void ASBPlayerCharacter::ApplyAttackDamage(float DamageAmount, float AttackRange, float AttackRadius)
{
    if (DamageAmount <= 0.0f || !GetWorld())
    {
        return;
    }

    const FVector Origin = GetActorLocation() + FVector(0.0f, 0.0f, 60.0f);
    const FVector Forward = GetActorForwardVector().GetSafeNormal();
    const FVector End = Origin + (Forward * AttackRange);
    const FCollisionObjectQueryParams ObjParams(ECC_Pawn);
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(CombatTrace), false, this);
    QueryParams.bReturnPhysicalMaterial = false;
    QueryParams.bTraceComplex = false;

    TArray<FHitResult> HitResults;
    const FCollisionShape Shape = FCollisionShape::MakeSphere(AttackRadius);

    const bool bHit = GetWorld()->SweepMultiByObjectType(
        HitResults,
        Origin,
        End,
        FQuat::Identity,
        ObjParams,
        Shape,
        QueryParams);

    if (bDebugCombatTrace)
    {
        const FColor TraceColor = bHit ? FColor::Red : FColor::Green;
        DrawDebugCapsule(
            GetWorld(),
            Origin + (Forward * (AttackRange * 0.5f)),
            AttackRange * 0.5f,
            AttackRadius,
            Forward.ToOrientationQuat(),
            TraceColor,
            false,
            0.2f,
            0,
            2.0f);
    }

    if (!bHit)
    {
        return;
    }

    for (const FHitResult& Hit : HitResults)
    {
        ASBEnemyBase* Enemy = Cast<ASBEnemyBase>(Hit.GetActor());
        if (!Enemy || Enemy->bIsDead)
        {
            continue;
        }

        Enemy->ReceiveDamage(DamageAmount);

        SpawnCombatFX(CombatHitVFX, Hit.ImpactPoint);
        SpawnCombatSFX(Hit.ImpactPoint);
        BroadcastNotify(TEXT("WeaponImpact"));
        break;
    }
}

void ASBPlayerCharacter::ApplySwordSkillDamage()
{
    ApplyAttackDamage(HeavyAttackDamage * 1.5f, MeleeAttackRange + 40.0f, MeleeAttackRadius + 25.0f);
}

void ASBPlayerCharacter::NotifyContractManagerOfHit(bool bSuccessfulParry)
{
    if (ASBContractManager* ContractManager = GetContractManager())
    {
        if (bSuccessfulParry)
        {
            ContractManager->RecordParry();
        }
        else
        {
            ContractManager->RecordHitTaken();
        }
    }
}

void ASBPlayerCharacter::NotifyContractManagerOfLowHealth()
{
    if (ASBContractManager* ContractManager = GetContractManager())
    {
        const float LowHealthThreshold = 0.3f * MaxHealth;
        ContractManager->SetLowHealthState(CurrentHealth <= LowHealthThreshold);
    }
}

ASBContractManager* ASBPlayerCharacter::GetContractManager() const
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return nullptr;
    }

    for (TActorIterator<ASBContractManager> It(World); It; ++It)
    {
        return *It;
    }
    return nullptr;
}

void ASBPlayerCharacter::TakeDamageCustom(float DamageAmount)
{
    if (bIsDead || bIsInvincible || DamageAmount <= 0.0f)
    {
        return;
    }

    if (bParryWindowActive)
    {
        OnParrySuccess();
        SpawnCombatFX(ParryVFX, GetActorLocation());
        SpawnCombatSFX(GetActorLocation());
        BroadcastNotify(TEXT("ParrySuccess"));
        NotifyContractManagerOfHit(true);
        return;
    }

    if (bIsBlocking)
    {
        const float Drain = DamageAmount * BlockDrainRate * 0.05f;
        ConsumeStamina(Drain);
        SpawnCombatFX(CombatHitVFX, GetActorLocation() + FVector(0.0f, 0.0f, 60.0f));
        SpawnCombatSFX(GetActorLocation());
        BroadcastNotify(TEXT("Blocked"));
        return;
    }

    CurrentHealth = FMath::Clamp(CurrentHealth - DamageAmount, 0.0f, MaxHealth);
    if (CurrentHealth <= 0.0f)
    {
        Die();
    }
    else
    {
        SpawnCombatFX(CombatHitVFX, GetActorLocation() + FVector(0.0f, 0.0f, 60.0f));
        SpawnCombatSFX(GetActorLocation());
        BroadcastNotify(TEXT("TakeDamage"));
        NotifyContractManagerOfHit(false);
    }
}

bool ASBPlayerCharacter::TryLightAttack()
{
    if (bIsDead || bIsAttacking)
    {
        return false;
    }

    constexpr float LightAttackStaminaCost = 10.0f;
    if (!ConsumeStamina(LightAttackStaminaCost))
    {
        return false;
    }

    bIsAttacking = true;
    bCanCombo = true;
    ComboIndex = (ComboIndex + 1) % FMath::Max(1, MaxComboCount);
    PlayMontageIfSet(LightAttackMontage);
    ApplyAttackDamage(LightAttackDamage, MeleeAttackRange, MeleeAttackRadius);
    SpawnCombatFX(CombatHitVFX, GetActorLocation() + FVector(50.0f, 0.0f, 40.0f));
    SpawnCombatSFX(GetActorLocation());
    BroadcastNotify(TEXT("LightAttack"));

    GetWorldTimerManager().ClearTimer(AttackResetTimerHandle);
    GetWorldTimerManager().SetTimer(AttackResetTimerHandle, this, &ASBPlayerCharacter::ResetAttackState, ComboResetTime, false);
    return true;
}

void ASBPlayerCharacter::TryHeavyAttackInput()
{
    TryHeavyAttack();
}

void ASBPlayerCharacter::StartBlockInput()
{
    StartBlock();
}

void ASBPlayerCharacter::StopBlockInput()
{
    StopBlock();
}

void ASBPlayerCharacter::TryDodgeInput()
{
    TryDodge();
}

void ASBPlayerCharacter::TrySkillInput()
{
    TrySwordSkill();
}

bool ASBPlayerCharacter::TryHeavyAttack()
{
    if (bIsDead || bIsAttacking)
    {
        return false;
    }

    constexpr float HeavyAttackStaminaCost = 25.0f;
    if (!ConsumeStamina(HeavyAttackStaminaCost))
    {
        return false;
    }

    bIsAttacking = true;
    bCanCombo = false;
    ComboIndex = 0;
    PlayMontageIfSet(HeavyAttackMontage);
    ApplyAttackDamage(HeavyAttackDamage, MeleeAttackRange + HeavyAttackRangeBonus, MeleeAttackRadius + 15.0f);
    SpawnCombatFX(CombatHitVFX, GetActorLocation() + FVector(50.0f, 0.0f, 40.0f));
    SpawnCombatSFX(GetActorLocation());
    BroadcastNotify(TEXT("HeavyAttack"));

    GetWorldTimerManager().ClearTimer(AttackResetTimerHandle);
    GetWorldTimerManager().SetTimer(AttackResetTimerHandle, this, &ASBPlayerCharacter::ResetAttackState, 0.65f, false);
    return true;
}

bool ASBPlayerCharacter::TryDodge()
{
    if (bIsDead || bIsDodging)
    {
        return false;
    }

    if (!ConsumeStamina(DodgeCost))
    {
        return false;
    }

    bIsDodging = true;
    bIsInvincible = true;
    PlayMontageIfSet(DodgeMontage);
    BroadcastNotify(TEXT("Dodge"));

    GetWorldTimerManager().ClearTimer(DodgeTimerHandle);
    GetWorldTimerManager().SetTimer(DodgeTimerHandle, this, &ASBPlayerCharacter::EndDodge, 0.35f, false);
    return true;
}

void ASBPlayerCharacter::StartBlock()
{
    if (bIsDead || CurrentStamina <= 0.0f || bIsDodging)
    {
        return;
    }

    bIsBlocking = true;
    bParryWindowActive = true;
    PlayMontageIfSet(BlockMontage);
    BroadcastNotify(TEXT("BlockStart"));
    GetWorldTimerManager().ClearTimer(ParryTimerHandle);
    GetWorldTimerManager().SetTimer(ParryTimerHandle, this, &ASBPlayerCharacter::DisableParryWindow, ParryWindowDuration, false);
}

void ASBPlayerCharacter::StopBlock()
{
    bIsBlocking = false;
    bParryWindowActive = false;
    BroadcastNotify(TEXT("BlockStop"));
    GetWorldTimerManager().ClearTimer(ParryTimerHandle);
}

bool ASBPlayerCharacter::TrySwordSkill()
{
    if (bIsDead || !bSwordSkillReady || bIsAttacking)
    {
        return false;
    }

    constexpr float SwordSkillStaminaCost = 20.0f;
    if (!ConsumeStamina(SwordSkillStaminaCost))
    {
        return false;
    }

    bSwordSkillReady = false;
    SwordSkillCooldownRemaining = FMath::Max(0.1f, SwordSkillCooldown);
    PlayMontageIfSet(SkillMontage);
    ApplySwordSkillDamage();
    BroadcastNotify(TEXT("SwordSkill"));
    return true;
}

void ASBPlayerCharacter::OnParrySuccess()
{
    bParryWindowActive = false;
    CurrentStamina = FMath::Clamp(CurrentStamina + 20.0f, 0.0f, MaxStamina);
    PlayMontageIfSet(BlockMontage);
    SpawnCombatFX(ParryVFX, GetActorLocation());
    SpawnCombatSFX(GetActorLocation());
    BroadcastNotify(TEXT("Parry"));
}

void ASBPlayerCharacter::Die()
{
    if (bIsDead)
    {
        return;
    }

    bIsDead = true;
    bIsAttacking = false;
    bIsBlocking = false;
    bIsDodging = false;
    bParryWindowActive = false;
    bIsInvincible = false;

    if (UCharacterMovementComponent* MoveComp = GetCharacterMovement())
    {
        MoveComp->DisableMovement();
    }

    PlayMontageIfSet(DeathMontage);
    BroadcastNotify(TEXT("Death"));

    OnPlayerDied.Broadcast();
}

void ASBPlayerCharacter::UpdateStaminaRegen(float DeltaSeconds)
{
    if (bIsDead || bIsBlocking || bIsAttacking || bIsDodging)
    {
        return;
    }

    if (TimeSinceLastStaminaSpend < StaminaRegenDelay)
    {
        return;
    }

    CurrentStamina = FMath::Clamp(CurrentStamina + (StaminaRegenRate * DeltaSeconds), 0.0f, MaxStamina);
}

void ASBPlayerCharacter::UpdateSwordSkillCooldown(float DeltaSeconds)
{
    if (bSwordSkillReady)
    {
        return;
    }

    SwordSkillCooldownRemaining = FMath::Max(0.0f, SwordSkillCooldownRemaining - DeltaSeconds);
    if (SwordSkillCooldownRemaining <= 0.0f)
    {
        bSwordSkillReady = true;
    }
}

void ASBPlayerCharacter::UpdateHUDValues()
{
    const float HealthPct = FMath::Clamp(CurrentHealth / MaxHealth, 0.0f, 1.0f);
    const float StaminaPct = FMath::Clamp(CurrentStamina / MaxStamina, 0.0f, 1.0f);
    const float CooldownPct = SwordSkillCooldown > 0.0f
        ? FMath::Clamp(SwordSkillCooldownRemaining / SwordSkillCooldown, 0.0f, 1.0f)
        : 0.0f;

    if (!FMath::IsNearlyEqual(HealthPct, LastHealthPct, KINDA_SMALL_NUMBER))
    {
        LastHealthPct = HealthPct;
        OnHealthChanged.Broadcast(HealthPct);
    }

    if (!FMath::IsNearlyEqual(StaminaPct, LastStaminaPct, KINDA_SMALL_NUMBER))
    {
        LastStaminaPct = StaminaPct;
        OnStaminaChanged.Broadcast(StaminaPct);
    }

    if (!FMath::IsNearlyEqual(CooldownPct, LastCooldownPct, KINDA_SMALL_NUMBER))
    {
        LastCooldownPct = CooldownPct;
        OnSwordCooldownChanged.Broadcast(CooldownPct);
    }
}

void ASBPlayerCharacter::ResetAttackState()
{
    bIsAttacking = false;
    bCanCombo = true;

    if (!GetWorldTimerManager().IsTimerActive(AttackResetTimerHandle))
    {
        ComboIndex = 0;
    }
}

void ASBPlayerCharacter::PlayMontageIfSet(UAnimMontage* MontageToPlay)
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

void ASBPlayerCharacter::SpawnCombatFX(UParticleSystem* FX, const FVector& Location) const
{
    if (!FX || !GetWorld())
    {
        return;
    }

    UGameplayStatics::SpawnEmitterAtLocation(
        GetWorld(),
        FX,
        Location,
        FRotator::ZeroRotator,
        true);
}

void ASBPlayerCharacter::SpawnCombatSFX(const FVector& Location) const
{
    if (!CombatImpactSFX || !GetWorld())
    {
        return;
    }

    UGameplayStatics::PlaySoundAtLocation(this, CombatImpactSFX, Location);
}

void ASBPlayerCharacter::BroadcastNotify(FName NotifyName)
{
    ReceiveCombatNotify(NotifyName);
}

bool ASBPlayerCharacter::ConsumeStamina(float Amount)
{
    if (Amount <= 0.0f)
    {
        return true;
    }

    if (CurrentStamina < Amount)
    {
        return false;
    }

    CurrentStamina = FMath::Clamp(CurrentStamina - Amount, 0.0f, MaxStamina);
    MarkStaminaSpent();
    return true;
}

void ASBPlayerCharacter::MarkStaminaSpent()
{
    TimeSinceLastStaminaSpend = 0.0f;
}

void ASBPlayerCharacter::EndDodge()
{
    bIsDodging = false;
    bIsInvincible = false;
}

void ASBPlayerCharacter::DisableParryWindow()
{
    bParryWindowActive = false;
}
