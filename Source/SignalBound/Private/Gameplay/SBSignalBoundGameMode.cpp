#include "Gameplay/SBSignalBoundGameMode.h"

#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Gameplay/SBContractManager.h"
#include "Gameplay/SBHUDManager.h"
#include "Gameplay/SBPlayerCharacter.h"
#include "Gameplay/SBSystemManager.h"

ASBSignalBoundGameMode::ASBSignalBoundGameMode()
{
    PrimaryActorTick.bCanEverTick = false;
    DefaultPawnClass = ASBPlayerCharacter::StaticClass();
}

void ASBSignalBoundGameMode::BeginPlay()
{
    Super::BeginPlay();

    SystemManager = FindExistingActor<ASBSystemManager>();
    ContractManager = FindExistingActor<ASBContractManager>();
    HUDManager = FindExistingActor<ASBHUDManager>();

    if (!bSpawnManagersIfMissing)
    {
        return;
    }

    if (!SystemManager)
    {
        SystemManager = SpawnManager<ASBSystemManager>(SystemManagerClass);
    }
    if (!ContractManager)
    {
        ContractManager = SpawnManager<ASBContractManager>(ContractManagerClass);
    }
    if (!HUDManager)
    {
        HUDManager = SpawnManager<ASBHUDManager>(HUDManagerClass);
    }

    if (HUDManager)
    {
        if (APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr)
        {
            HUDManager->CreateHUD(PlayerController);
            HUDManager->BindToPlayer(Cast<ASBPlayerCharacter>(PlayerController->GetCharacter()));
        }
        HUDManager->BindToSystemManager(SystemManager);
        HUDManager->BindToContractManager(ContractManager);
    }

    if (UWorld* World = GetWorld())
    {
        World->GetTimerManager().SetTimer(IntroTimerHandle, this, &ASBSignalBoundGameMode::DelayedIntro, 2.0f, false);
    }
}

void ASBSignalBoundGameMode::DelayedIntro()
{
    if (SystemManager)
    {
        SystemManager->RequestDirective(TEXT("Hub"));
    }
}

void ASBSignalBoundGameMode::ToggleDemoMode(bool bEnabled)
{
    bIsDemoMode = bEnabled;

    if (bIsDemoMode)
    {
        UE_LOG(LogTemp, Log, TEXT("DEMO MODE ENABLED - Initializing world reset and tour..."));

        if (SystemManager)
        {
            // Signal system to show intro directive
            SystemManager->RequestDirective(TEXT("Intro"));
        }
    }
}

template <typename TActorType>
TActorType* ASBSignalBoundGameMode::FindExistingActor() const
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return nullptr;
    }

    for (TActorIterator<TActorType> It(World); It; ++It)
    {
        return *It;
    }
    return nullptr;
}

template <typename TActorType>
TActorType* ASBSignalBoundGameMode::SpawnManager(TSubclassOf<TActorType> ClassToSpawn)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return nullptr;
    }

    UClass* SpawnClass = *ClassToSpawn ? *ClassToSpawn : TActorType::StaticClass();
    FActorSpawnParameters SpawnParams;
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    SpawnParams.Name = MakeUniqueObjectName(World, SpawnClass, FName(*SpawnClass->GetName()));
    return World->SpawnActor<TActorType>(SpawnClass, FVector::ZeroVector, FRotator::ZeroRotator, SpawnParams);
}

template ASBSystemManager* ASBSignalBoundGameMode::SpawnManager<ASBSystemManager>(TSubclassOf<ASBSystemManager>);
template ASBContractManager* ASBSignalBoundGameMode::SpawnManager<ASBContractManager>(TSubclassOf<ASBContractManager>);
template ASBHUDManager* ASBSignalBoundGameMode::SpawnManager<ASBHUDManager>(TSubclassOf<ASBHUDManager>);
