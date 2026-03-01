#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SBLevelTransitionTrigger.generated.h"

class UBoxComponent;
class APawn;
class UPrimitiveComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FSBTransitionTriggeredSignature, APawn*, InstigatorPawn, FName, DestinationMap);

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBLevelTransitionTrigger : public AActor
{
    GENERATED_BODY()

public:
    ASBLevelTransitionTrigger();

    UFUNCTION(BlueprintCallable, Category = "Transition")
    void SetTransitionEnabled(bool bEnabled) { bTransitionEnabled = bEnabled; }

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBTransitionTriggeredSignature OnTransitionTriggered;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Transition")
    FName DestinationMap = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Transition")
    bool bTransitionEnabled = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Transition")
    bool bOpenLevelOnOverlap = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Transition")
    UBoxComponent* TriggerVolume = nullptr;

protected:
    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void OnTriggerBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
        int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
};
