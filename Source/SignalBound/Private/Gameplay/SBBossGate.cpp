#include "Gameplay/SBBossGate.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"

ASBBossGate::ASBBossGate()
{
    PrimaryActorTick.bCanEverTick = false;

    GateMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("GateMesh"));
    RootComponent = GateMesh;

    BlockingVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("BlockingVolume"));
    BlockingVolume->SetupAttachment(RootComponent);
    BlockingVolume->SetBoxExtent(FVector(200.0f, 50.0f, 220.0f));
    BlockingVolume->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    BlockingVolume->SetCollisionResponseToAllChannels(ECR_Block);
}

void ASBBossGate::RegisterLeverActivation(FName LeverId)
{
    if (LeverId == NAME_None)
    {
        return;
    }

    ActivatedLeverIds.AddUnique(LeverId);
    EvaluateGateState();
}

void ASBBossGate::RegisterSigilInsert(FName SigilId)
{
    if (SigilId == NAME_None)
    {
        return;
    }

    InsertedSigilIds.AddUnique(SigilId);
    EvaluateGateState();
}

bool ASBBossGate::EvaluateGateState()
{
    if (bIsOpen)
    {
        return true;
    }

    const bool bLeversSatisfied = ActivatedLeverIds.Num() >= RequiredLevers;
    const bool bSigilsSatisfied = InsertedSigilIds.Num() >= RequiredSigils;
    if (bLeversSatisfied && bSigilsSatisfied)
    {
        OpenGate();
        return true;
    }

    return false;
}

void ASBBossGate::OpenGate()
{
    if (bIsOpen)
    {
        return;
    }

    bIsOpen = true;
    if (BlockingVolume)
    {
        BlockingVolume->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }

    OnGateStateChanged.Broadcast(true);
}
