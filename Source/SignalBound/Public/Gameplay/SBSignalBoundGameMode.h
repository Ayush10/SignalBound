#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "SBSignalBoundGameMode.generated.h"

class ASBSystemManager;
class ASBContractManager;
class ASBHUDManager;

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBSignalBoundGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ASBSignalBoundGameMode();

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintPure, Category = "Managers")
    ASBSystemManager* GetSystemManager() const { return SystemManager; }

    UFUNCTION(BlueprintPure, Category = "Managers")
    ASBContractManager* GetContractManager() const { return ContractManager; }

    UFUNCTION(BlueprintPure, Category = "Managers")
    ASBHUDManager* GetHUDManager() const { return HUDManager; }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Managers")
    TSubclassOf<ASBSystemManager> SystemManagerClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Managers")
    TSubclassOf<ASBContractManager> ContractManagerClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Managers")
    TSubclassOf<ASBHUDManager> HUDManagerClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Managers")
    bool bSpawnManagersIfMissing = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Demo")
    bool bIsDemoMode = false;

    UFUNCTION(BlueprintCallable, Category = "Demo")
    void ToggleDemoMode(bool bEnabled);

    UFUNCTION()
    void DelayedIntro();

private:
    FTimerHandle IntroTimerHandle;

    template <typename TActorType>
    TActorType* FindExistingActor() const;

    template <typename TActorType>
    TActorType* SpawnManager(TSubclassOf<TActorType> ClassToSpawn);

    UPROPERTY(Transient)
    ASBSystemManager* SystemManager = nullptr;

    UPROPERTY(Transient)
    ASBContractManager* ContractManager = nullptr;

    UPROPERTY(Transient)
    ASBHUDManager* HUDManager = nullptr;
};
