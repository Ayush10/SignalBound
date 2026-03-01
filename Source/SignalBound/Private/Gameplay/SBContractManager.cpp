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

TArray<FSBContractState> ASBContractManager::GetAvailableContracts() const
{
    TArray<FSBContractState> Contracts;
    
    // Contract 1: NoHeal
    FSBContractState NoHeal;
    NoHeal.Type = ESBContractType::NoHeal;
    NoHeal.TimeLimitSeconds = 30.0f;
    Contracts.Add(NoHeal);

    // Contract 2: ParryChain
    FSBContractState ParryChain;
    ParryChain.Type = ESBContractType::ParryChain;
    ParryChain.TargetCount = 3;
    ParryChain.TimeLimitSeconds = 25.0f;
    Contracts.Add(ParryChain);

    // Contract 3: NoHits
    FSBContractState NoHits;
    NoHits.Type = ESBContractType::NoHits;
    NoHits.TimeLimitSeconds = 20.0f;
    Contracts.Add(NoHits);

    // Contract 4: KillCount
    FSBContractState KillCountContract;
    KillCountContract.Type = ESBContractType::KillCount;
    KillCountContract.TargetCount = 5;
    KillCountContract.TimeLimitSeconds = 60.0f;
    Contracts.Add(KillCountContract);

    // Contract 5: LowHPSurvival
    FSBContractState LowHPSurvival;
    LowHPSurvival.Type = ESBContractType::LowHPSurvival;
    LowHPSurvival.TimeLimitSeconds = 15.0f;
    Contracts.Add(LowHPSurvival);

    // Contract 6: FastClear
    FSBContractState FastClear;
    FastClear.Type = ESBContractType::FastClear;
    FastClear.TargetCount = 3;
    FastClear.TimeLimitSeconds = 45.0f;
    Contracts.Add(FastClear);

    return Contracts;
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
