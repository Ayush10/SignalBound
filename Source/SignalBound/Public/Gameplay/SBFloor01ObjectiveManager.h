#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SBFloor01ObjectiveManager.generated.h"

class ASBBossGate;
class ASBLevelTransitionTrigger;
class ASBObjectiveLever;
class APawn;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSBFloorObjectiveStateChangedSignature, bool, bBossGateOpen);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FSBFloorObjectiveSimpleSignature);

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBFloor01ObjectiveManager : public AActor
{
    GENERATED_BODY()

public:
    ASBFloor01ObjectiveManager();

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "Objectives")
    void RegisterLeverActivation(FName LeverId);

    UFUNCTION(BlueprintCallable, Category = "Objectives")
    void RegisterSigilInsert(FName SigilId);

    UFUNCTION(BlueprintCallable, Category = "Objectives")
    void RegisterBossDefeated();

    UFUNCTION(BlueprintCallable, Category = "Objectives")
    bool EvaluateBossGateState();

    UFUNCTION(BlueprintCallable, Category = "Objectives")
    void BindWorldActors();

    UFUNCTION(BlueprintPure, Category = "Objectives")
    int32 GetSigilCount() const { return InsertedSigilIds.Num(); }

    UFUNCTION(BlueprintPure, Category = "Objectives")
    bool IsBossGateOpen() const { return bBossGateOpen; }

    UFUNCTION(BlueprintPure, Category = "Objectives")
    bool IsAscensionEnabled() const { return bAscensionEnabled; }

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBFloorObjectiveStateChangedSignature OnBossGateStateChanged;

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBFloorObjectiveSimpleSignature OnAscensionEnabled;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objectives")
    int32 RequiredLevers = 2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objectives")
    int32 RequiredSigils = 3;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objectives")
    bool bAutoBindLevers = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objectives")
    bool bAutoFindBossGate = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objectives")
    bool bAutoFindAscensionTrigger = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objectives")
    ASBBossGate* BossGateActor = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Objectives")
    ASBLevelTransitionTrigger* AscensionTrigger = nullptr;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Runtime")
    TArray<FName> ActivatedLeverIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Runtime")
    TArray<FName> InsertedSigilIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Runtime")
    bool bBossGateOpen = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Runtime")
    bool bBossDefeated = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Runtime")
    bool bAscensionEnabled = false;

private:
    UFUNCTION()
    void HandleLeverActivated(ASBObjectiveLever* Lever, APawn* ActivatorPawn);

    bool HasLeverRequirementsMet() const;
    bool HasSigilRequirementsMet() const;
};
