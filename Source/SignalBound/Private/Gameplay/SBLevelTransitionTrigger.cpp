#include "Gameplay/SBLevelTransitionTrigger.h"

#include "Components/BoxComponent.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

ASBLevelTransitionTrigger::ASBLevelTransitionTrigger()
{
    PrimaryActorTick.bCanEverTick = false;

    TriggerVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerVolume"));
    RootComponent = TriggerVolume;
    TriggerVolume->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    TriggerVolume->SetCollisionResponseToAllChannels(ECR_Ignore);
    TriggerVolume->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    TriggerVolume->SetGenerateOverlapEvents(true);
    TriggerVolume->SetBoxExtent(FVector(150.0f, 200.0f, 140.0f));
}

void ASBLevelTransitionTrigger::BeginPlay()
{
    Super::BeginPlay();

    if (TriggerVolume)
    {
        TriggerVolume->OnComponentBeginOverlap.AddDynamic(this, &ASBLevelTransitionTrigger::OnTriggerBeginOverlap);
    }
}

void ASBLevelTransitionTrigger::OnTriggerBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (!bTransitionEnabled || !OtherActor)
    {
        return;
    }

    APawn* Pawn = Cast<APawn>(OtherActor);
    if (!Pawn)
    {
        return;
    }

    OnTransitionTriggered.Broadcast(Pawn, DestinationMap);

    if (bOpenLevelOnOverlap && DestinationMap != NAME_None)
    {
        UGameplayStatics::OpenLevel(this, DestinationMap);
    }
}
