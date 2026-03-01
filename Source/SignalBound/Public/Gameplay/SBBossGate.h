#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SBBossGate.generated.h"

class UStaticMeshComponent;
class UBoxComponent;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSBBossGateStateSignature, bool, bIsOpen);

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBBossGate : public AActor
{
    GENERATED_BODY()

public:
    ASBBossGate();

    UFUNCTION(BlueprintCallable, Category = "Gate")
    void RegisterLeverActivation(FName LeverId);

    UFUNCTION(BlueprintCallable, Category = "Gate")
    void RegisterSigilInsert(FName SigilId);

    UFUNCTION(BlueprintCallable, Category = "Gate")
    bool EvaluateGateState();

    UFUNCTION(BlueprintCallable, Category = "Gate")
    void OpenGate();

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBBossGateStateSignature OnGateStateChanged;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gate")
    int32 RequiredLevers = 2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gate")
    int32 RequiredSigils = 3;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Gate")
    bool bIsOpen = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Gate")
    TArray<FName> ActivatedLeverIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Gate")
    TArray<FName> InsertedSigilIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UStaticMeshComponent* GateMesh = nullptr;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UBoxComponent* BlockingVolume = nullptr;
};
