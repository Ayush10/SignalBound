#include "Gameplay/SBContractManager.h"

ASBContractManager::ASBContractManager()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ASBContractManager::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    UpdateContract(DeltaSeconds);
}

FSBContractState ASBContractManager::OfferContract(ESBContractType Type, int32 TargetCount, float TimeLimitSeconds)
{
    CurrentContract = FSBContractState();
    CurrentContract.Type = Type;
    CurrentContract.TargetCount = TargetCount;
    CurrentContract.TimeLimitSeconds = FMath::Max(0.0f, TimeLimitSeconds);
    CurrentContract.bActive = false;
    CurrentContract.bSucceeded = false;
    CurrentContract.bFailed = false;

    KillCount = 0;
    ParryCount = 0;
    HitCount = 0;
    bLowHealthState = false;

    OnContractChanged.Broadcast(CurrentContract);
    return CurrentContract;
}

bool ASBContractManager::AcceptContract()
{
    if (CurrentContract.Type == ESBContractType::None || CurrentContract.bActive)
    {
        return false;
    }

    CurrentContract.bActive = true;
    CurrentContract.ElapsedSeconds = 0.0f;
    OnContractChanged.Broadcast(CurrentContract);
    return true;
}

void ASBContractManager::FailContract()
{
    if (!CurrentContract.bActive)
    {
        return;
    }

    CurrentContract.bActive = false;
    CurrentContract.bFailed = true;
    CurrentContract.bSucceeded = false;
    OnContractChanged.Broadcast(CurrentContract);
}

void ASBContractManager::CompleteContract()
{
    if (!CurrentContract.bActive)
    {
        return;
    }

    CurrentContract.bActive = false;
    CurrentContract.bSucceeded = true;
    CurrentContract.bFailed = false;
    OnContractChanged.Broadcast(CurrentContract);
}

void ASBContractManager::UpdateContract(float DeltaSeconds)
{
    if (!CurrentContract.bActive)
    {
        return;
    }

    CurrentContract.ElapsedSeconds += FMath::Max(0.0f, DeltaSeconds);
    if (CurrentContract.TimeLimitSeconds > 0.0f && CurrentContract.ElapsedSeconds > CurrentContract.TimeLimitSeconds)
    {
        FailContract();
        return;
    }

    switch (CurrentContract.Type)
    {
    case ESBContractType::NoHeal:
        if (CurrentContract.ElapsedSeconds >= CurrentContract.TimeLimitSeconds)
        {
            CompleteContract();
        }
        break;
    case ESBContractType::ParryChain:
        CurrentContract.ProgressCount = ParryCount;
        if (ParryCount >= CurrentContract.TargetCount)
        {
            CompleteContract();
        }
        break;
    case ESBContractType::NoHits:
        CurrentContract.ProgressCount = FMath::Max(0, CurrentContract.TargetCount - HitCount);
        if (HitCount > 0)
        {
            FailContract();
            return;
        }
        if (CurrentContract.ElapsedSeconds >= CurrentContract.TimeLimitSeconds)
        {
            CompleteContract();
        }
        break;
    case ESBContractType::KillCount:
        CurrentContract.ProgressCount = KillCount;
        if (KillCount >= CurrentContract.TargetCount)
        {
            CompleteContract();
        }
        break;
    case ESBContractType::LowHPSurvival:
        if (!bLowHealthState)
        {
            FailContract();
            return;
        }
        if (CurrentContract.ElapsedSeconds >= CurrentContract.TimeLimitSeconds)
        {
            CompleteContract();
        }
        break;
    case ESBContractType::FastClear:
        CurrentContract.ProgressCount = KillCount;
        if (KillCount >= CurrentContract.TargetCount)
        {
            CompleteContract();
        }
        break;
    default:
        break;
    }
}

void ASBContractManager::RecordParry()
{
    ++ParryCount;
}

void ASBContractManager::RecordKill()
{
    ++KillCount;
}

void ASBContractManager::RecordHitTaken()
{
    ++HitCount;
}

void ASBContractManager::SetLowHealthState(bool bIsLowHealth)
{
    bLowHealthState = bIsLowHealth;
}

FString ASBContractManager::GetContractStatusText() const
{
    if (CurrentContract.Type == ESBContractType::None)
    {
        return TEXT("No active contract");
    }

    if (CurrentContract.bSucceeded)
    {
        return TEXT("Contract succeeded");
    }

    if (CurrentContract.bFailed)
    {
        return TEXT("Contract failed");
    }

    if (!CurrentContract.bActive)
    {
        return TEXT("Contract offered");
    }

    const float Remaining = FMath::Max(0.0f, CurrentContract.TimeLimitSeconds - CurrentContract.ElapsedSeconds);
    return FString::Printf(TEXT("Contract active | Progress %d/%d | %.1fs left"),
        CurrentContract.ProgressCount,
        CurrentContract.TargetCount,
        Remaining);
}
