#include "Gameplay/SBPlayerCharacter.h"

#include "GameFramework/CharacterMovementComponent.h"
#include "TimerManager.h"

ASBPlayerCharacter::ASBPlayerCharacter()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ASBPlayerCharacter::BeginPlay()
{
    Super::BeginPlay();

    MaxHealth = FMath::Max(1.0f, MaxHealth);
    MaxStamina = FMath::Max(1.0f, MaxStamina);
    CurrentHealth = FMath::Clamp(CurrentHealth, 0.0f, MaxHealth);
    CurrentStamina = FMath::Clamp(CurrentStamina, 0.0f, MaxStamina);
    SwordSkillCooldownRemaining = FMath::Max(0.0f, SwordSkillCooldownRemaining);
    bSwordSkillReady = SwordSkillCooldownRemaining <= 0.0f;

    LastHealthPct = CurrentHealth / MaxHealth;
    LastStaminaPct = CurrentStamina / MaxStamina;
    LastCooldownPct = SwordSkillCooldown > 0.0f ? (SwordSkillCooldownRemaining / SwordSkillCooldown) : 0.0f;

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
    UpdateStaminaRegen(DeltaSeconds);
    UpdateSwordSkillCooldown(DeltaSeconds);
    UpdateHUDValues();
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
        return;
    }

    if (bIsBlocking)
    {
        const float Drain = DamageAmount * BlockDrainRate * 0.05f;
        ConsumeStamina(Drain);
        return;
    }

    CurrentHealth = FMath::Clamp(CurrentHealth - DamageAmount, 0.0f, MaxHealth);
    if (CurrentHealth <= 0.0f)
    {
        Die();
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

    GetWorldTimerManager().ClearTimer(AttackResetTimerHandle);
    GetWorldTimerManager().SetTimer(AttackResetTimerHandle, this, &ASBPlayerCharacter::ResetAttackState, ComboResetTime, false);
    return true;
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
    GetWorldTimerManager().ClearTimer(ParryTimerHandle);
    GetWorldTimerManager().SetTimer(ParryTimerHandle, this, &ASBPlayerCharacter::DisableParryWindow, ParryWindowDuration, false);
}

void ASBPlayerCharacter::StopBlock()
{
    bIsBlocking = false;
    bParryWindowActive = false;
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
    return true;
}

void ASBPlayerCharacter::OnParrySuccess()
{
    bParryWindowActive = false;
    CurrentStamina = FMath::Clamp(CurrentStamina + 20.0f, 0.0f, MaxStamina);
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
