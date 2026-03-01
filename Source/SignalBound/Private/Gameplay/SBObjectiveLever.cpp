#include "Gameplay/SBObjectiveLever.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Pawn.h"

ASBObjectiveLever::ASBObjectiveLever()
{
    PrimaryActorTick.bCanEverTick = false;

    LeverMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("LeverMesh"));
    RootComponent = LeverMesh;

    InteractionTrigger = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionTrigger"));
    InteractionTrigger->SetupAttachment(RootComponent);
    InteractionTrigger->SetBoxExtent(FVector(120.0f, 120.0f, 120.0f));
    InteractionTrigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    InteractionTrigger->SetCollisionResponseToAllChannels(ECR_Ignore);
    InteractionTrigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    InteractionTrigger->SetGenerateOverlapEvents(true);
}

void ASBObjectiveLever::BeginPlay()
{
    Super::BeginPlay();

    if (InteractionTrigger)
    {
        InteractionTrigger->OnComponentBeginOverlap.AddDynamic(this, &ASBObjectiveLever::OnTriggerBeginOverlap);
    }
}

bool ASBObjectiveLever::ActivateLever(APawn* ActivatorPawn)
{
    if (bIsActivated)
    {
        return false;
    }

    bIsActivated = true;
    OnLeverActivated.Broadcast(this, ActivatorPawn);
    return true;
}

void ASBObjectiveLever::OnTriggerBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (!bAutoActivateOnOverlap || !OtherActor)
    {
        return;
    }

    APawn* Pawn = Cast<APawn>(OtherActor);
    if (!Pawn)
    {
        return;
    }

    ActivateLever(Pawn);
}
