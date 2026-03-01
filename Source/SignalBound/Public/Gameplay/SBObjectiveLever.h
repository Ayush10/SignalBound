#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SBObjectiveLever.generated.h"

class UBoxComponent;
class UStaticMeshComponent;
class APawn;
class ASBObjectiveLever;
class UPrimitiveComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FSBLeverActivatedSignature, ASBObjectiveLever*, Lever, APawn*, ActivatorPawn);

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBObjectiveLever : public AActor
{
    GENERATED_BODY()

public:
    ASBObjectiveLever();

    UFUNCTION(BlueprintCallable, Category = "Objective")
    bool ActivateLever(APawn* ActivatorPawn);

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBLeverActivatedSignature OnLeverActivated;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objective")
    bool bIsActivated = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objective")
    FName LeverId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objective")
    bool bAutoActivateOnOverlap = true;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UStaticMeshComponent* LeverMesh = nullptr;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UBoxComponent* InteractionTrigger = nullptr;

protected:
    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void OnTriggerBeginOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp,
        int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
};
