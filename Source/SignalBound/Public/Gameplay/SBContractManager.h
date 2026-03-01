#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Gameplay/SBGameplayTypes.h"
#include "SBContractManager.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSBContractChangedSignature, const FSBContractState&, ContractState);

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBContractManager : public AActor
{
    GENERATED_BODY()

public:
    ASBContractManager();

    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category = "Contract")
    FSBContractState OfferContract(ESBContractType Type, int32 TargetCount, float TimeLimitSeconds);

    UFUNCTION(BlueprintPure, Category = "Contract")
    TArray<FSBContractState> GetAvailableContracts() const;

    UFUNCTION(BlueprintCallable, Category = "Contract")
    bool AcceptContract();

    UFUNCTION(BlueprintCallable, Category = "Contract")
    void FailContract();

    UFUNCTION(BlueprintCallable, Category = "Contract")
    void CompleteContract();

    UFUNCTION(BlueprintCallable, Category = "Contract")
    void UpdateContract(float DeltaSeconds);

    UFUNCTION(BlueprintCallable, Category = "Contract")
    void RecordParry();

    UFUNCTION(BlueprintCallable, Category = "Contract")
    void RecordKill();

    UFUNCTION(BlueprintCallable, Category = "Contract")
    void RecordHitTaken();

    UFUNCTION(BlueprintCallable, Category = "Contract")
    void SetLowHealthState(bool bIsLowHealth);

    UFUNCTION(BlueprintPure, Category = "Contract")
    FString GetContractStatusText() const;

    UFUNCTION(BlueprintPure, Category = "Contract")
    const FSBContractState& GetCurrentContract() const { return CurrentContract; }

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBContractChangedSignature OnContractChanged;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Contract")
    FSBContractState CurrentContract;

private:
    int32 KillCount = 0;
    int32 ParryCount = 0;
    int32 HitCount = 0;
    bool bLowHealthState = false;
};
