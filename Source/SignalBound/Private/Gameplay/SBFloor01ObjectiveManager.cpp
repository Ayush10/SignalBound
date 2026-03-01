#include "Gameplay/SBFloor01ObjectiveManager.h"

#include "EngineUtils.h"
#include "Gameplay/SBBossGate.h"
#include "Gameplay/SBLevelTransitionTrigger.h"
#include "Gameplay/SBObjectiveLever.h"

ASBFloor01ObjectiveManager::ASBFloor01ObjectiveManager()
{
    PrimaryActorTick.bCanEverTick = false;
}

void ASBFloor01ObjectiveManager::BeginPlay()
{
    Super::BeginPlay();

    BindWorldActors();
    EvaluateBossGateState();
}

void ASBFloor01ObjectiveManager::RegisterLeverActivation(FName LeverId)
{
    if (LeverId == NAME_None)
    {
        return;
    }

    ActivatedLeverIds.AddUnique(LeverId);
    EvaluateBossGateState();
}

void ASBFloor01ObjectiveManager::RegisterSigilInsert(FName SigilId)
{
    if (SigilId == NAME_None)
    {
        return;
    }

    InsertedSigilIds.AddUnique(SigilId);
    EvaluateBossGateState();
}

void ASBFloor01ObjectiveManager::RegisterBossDefeated()
{
    if (bBossDefeated)
    {
        return;
    }

    bBossDefeated = true;
    bAscensionEnabled = true;

    if (AscensionTrigger)
    {
        AscensionTrigger->SetTransitionEnabled(true);
    }

    OnAscensionEnabled.Broadcast();
}

bool ASBFloor01ObjectiveManager::EvaluateBossGateState()
{
    const bool bShouldOpen = HasLeverRequirementsMet() && HasSigilRequirementsMet();
    if (bShouldOpen == bBossGateOpen)
    {
        return bBossGateOpen;
    }

    bBossGateOpen = bShouldOpen;
    if (bBossGateOpen && BossGateActor)
    {
        BossGateActor->OpenGate();
    }

    OnBossGateStateChanged.Broadcast(bBossGateOpen);
    return bBossGateOpen;
}

void ASBFloor01ObjectiveManager::BindWorldActors()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    if (bAutoFindBossGate && !BossGateActor)
    {
        for (TActorIterator<ASBBossGate> It(World); It; ++It)
        {
            BossGateActor = *It;
            break;
        }
    }

    if (bAutoFindAscensionTrigger && !AscensionTrigger)
    {
        for (TActorIterator<ASBLevelTransitionTrigger> It(World); It; ++It)
        {
            ASBLevelTransitionTrigger* Trigger = *It;
            if (Trigger && Trigger->GetActorNameOrLabel().Contains(TEXT("Ascension"), ESearchCase::IgnoreCase))
            {
                AscensionTrigger = Trigger;
                break;
            }
        }
    }

    if (AscensionTrigger && !bAscensionEnabled)
    {
        AscensionTrigger->SetTransitionEnabled(false);
    }

    if (!bAutoBindLevers)
    {
        return;
    }

    for (TActorIterator<ASBObjectiveLever> It(World); It; ++It)
    {
        ASBObjectiveLever* Lever = *It;
        if (!Lever)
        {
            continue;
        }

        Lever->OnLeverActivated.RemoveDynamic(this, &ASBFloor01ObjectiveManager::HandleLeverActivated);
        Lever->OnLeverActivated.AddDynamic(this, &ASBFloor01ObjectiveManager::HandleLeverActivated);
    }
}

void ASBFloor01ObjectiveManager::HandleLeverActivated(ASBObjectiveLever* Lever, APawn* ActivatorPawn)
{
    if (!Lever)
    {
        return;
    }

    FName LeverId = Lever->LeverId;
    if (LeverId == NAME_None)
    {
        LeverId = Lever->GetFName();
    }

    RegisterLeverActivation(LeverId);
}

bool ASBFloor01ObjectiveManager::HasLeverRequirementsMet() const
{
    const int32 Required = FMath::Max(0, RequiredLevers);
    return ActivatedLeverIds.Num() >= Required;
}

bool ASBFloor01ObjectiveManager::HasSigilRequirementsMet() const
{
    const int32 Required = FMath::Max(0, RequiredSigils);
    return InsertedSigilIds.Num() >= Required;
}
