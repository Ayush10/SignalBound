#include "Gameplay/SBHUDManager.h"

#include "Blueprint/UserWidget.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "Gameplay/SBContractManager.h"
#include "Gameplay/SBPlayerCharacter.h"
#include "Gameplay/SBSystemManager.h"
#include "UI/SBWidget_PlayerHUD.h"
#include "UI/SBWidget_SystemMenu.h"
#include "UI/SBWidget_SystemNotice.h"

ASBHUDManager::ASBHUDManager()
{
    PrimaryActorTick.bCanEverTick = false;
}

void ASBHUDManager::BeginPlay()
{
    Super::BeginPlay();

    APlayerController* PlayerController = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
    CreateHUD(PlayerController);

    BindToPlayer(PlayerController ? Cast<ASBPlayerCharacter>(PlayerController->GetCharacter()) : nullptr);

    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    for (TActorIterator<ASBSystemManager> It(World); It; ++It)
    {
        BindToSystemManager(*It);
        break;
    }

    for (TActorIterator<ASBContractManager> It(World); It; ++It)
    {
        BindToContractManager(*It);
        break;
    }
}

void ASBHUDManager::CreateHUD(APlayerController* ForPlayerController)
{
    if (!ForPlayerController)
    {
        return;
    }

    if (PlayerHUDClass && !PlayerHUDWidget)
    {
        PlayerHUDWidget = CreateWidget<USBWidget_PlayerHUD>(ForPlayerController, PlayerHUDClass);
        if (PlayerHUDWidget)
        {
            PlayerHUDWidget->AddToViewport(0);
        }
    }

    if (SystemNoticeClass && !SystemNoticeWidget)
    {
        SystemNoticeWidget = CreateWidget<USBWidget_SystemNotice>(ForPlayerController, SystemNoticeClass);
        if (SystemNoticeWidget)
        {
            SystemNoticeWidget->AddToViewport(1);
        }
    }

    if (SystemMenuClass && !SystemMenuWidget)
    {
        SystemMenuWidget = CreateWidget<USBWidget_SystemMenu>(ForPlayerController, SystemMenuClass);
        if (SystemMenuWidget)
        {
            SystemMenuWidget->AddToViewport(2);
        }
    }
}

void ASBHUDManager::UpdateHealth(float NormalizedValue)
{
    if (PlayerHUDWidget)
    {
        PlayerHUDWidget->UpdateHealth(NormalizedValue);
    }
}

void ASBHUDManager::UpdateStamina(float NormalizedValue)
{
    if (PlayerHUDWidget)
    {
        PlayerHUDWidget->UpdateStamina(NormalizedValue);
    }
}

void ASBHUDManager::UpdateCooldown(float NormalizedValue)
{
    if (PlayerHUDWidget)
    {
        PlayerHUDWidget->UpdateCooldown(NormalizedValue);
        PlayerHUDWidget->SetSkillReady(NormalizedValue <= KINDA_SMALL_NUMBER);
    }
}

void ASBHUDManager::ShowNotice(const FString& Text, float Duration)
{
    if (SystemNoticeWidget)
    {
        SystemNoticeWidget->ShowNotice(Text, Duration);
    }
}

void ASBHUDManager::ShowDirective(const FString& Text, float Duration)
{
    ShowNotice(Text, Duration);
}

void ASBHUDManager::ToggleMenu()
{
    if (SystemMenuWidget)
    {
        SystemMenuWidget->ToggleMenu();
    }
}

void ASBHUDManager::BindToPlayer(ASBPlayerCharacter* InPlayerCharacter)
{
    if (BoundPlayerCharacter == InPlayerCharacter)
    {
        return;
    }

    if (BoundPlayerCharacter)
    {
        BoundPlayerCharacter->OnHealthChanged.RemoveDynamic(this, &ASBHUDManager::HandlePlayerHealthChanged);
        BoundPlayerCharacter->OnStaminaChanged.RemoveDynamic(this, &ASBHUDManager::HandlePlayerStaminaChanged);
        BoundPlayerCharacter->OnSwordCooldownChanged.RemoveDynamic(this, &ASBHUDManager::HandlePlayerCooldownChanged);
    }

    BoundPlayerCharacter = InPlayerCharacter;

    if (!BoundPlayerCharacter)
    {
        return;
    }

    BoundPlayerCharacter->OnHealthChanged.AddDynamic(this, &ASBHUDManager::HandlePlayerHealthChanged);
    BoundPlayerCharacter->OnStaminaChanged.AddDynamic(this, &ASBHUDManager::HandlePlayerStaminaChanged);
    BoundPlayerCharacter->OnSwordCooldownChanged.AddDynamic(this, &ASBHUDManager::HandlePlayerCooldownChanged);

    UpdateHealth(BoundPlayerCharacter->MaxHealth > 0.0f ? BoundPlayerCharacter->CurrentHealth / BoundPlayerCharacter->MaxHealth : 0.0f);
    UpdateStamina(BoundPlayerCharacter->MaxStamina > 0.0f ? BoundPlayerCharacter->CurrentStamina / BoundPlayerCharacter->MaxStamina : 0.0f);
    UpdateCooldown(BoundPlayerCharacter->SwordSkillCooldown > 0.0f
        ? BoundPlayerCharacter->SwordSkillCooldownRemaining / BoundPlayerCharacter->SwordSkillCooldown
        : 0.0f);
}

void ASBHUDManager::BindToSystemManager(ASBSystemManager* InSystemManager)
{
    if (BoundSystemManager == InSystemManager)
    {
        return;
    }

    if (BoundSystemManager)
    {
        BoundSystemManager->OnDirectiveChanged.RemoveDynamic(this, &ASBHUDManager::HandleSystemDirectiveChanged);
    }

    BoundSystemManager = InSystemManager;
    if (!BoundSystemManager)
    {
        return;
    }

    BoundSystemManager->OnDirectiveChanged.AddDynamic(this, &ASBHUDManager::HandleSystemDirectiveChanged);
}

void ASBHUDManager::BindToContractManager(ASBContractManager* InContractManager)
{
    if (BoundContractManager == InContractManager)
    {
        return;
    }

    if (BoundContractManager)
    {
        BoundContractManager->OnContractChanged.RemoveDynamic(this, &ASBHUDManager::HandleContractChanged);
    }

    BoundContractManager = InContractManager;
    if (!BoundContractManager)
    {
        return;
    }

    BoundContractManager->OnContractChanged.AddDynamic(this, &ASBHUDManager::HandleContractChanged);
    HandleContractChanged(BoundContractManager->GetCurrentContract());
}

void ASBHUDManager::HandlePlayerHealthChanged(float NormalizedValue)
{
    UpdateHealth(NormalizedValue);
}

void ASBHUDManager::HandlePlayerStaminaChanged(float NormalizedValue)
{
    UpdateStamina(NormalizedValue);
}

void ASBHUDManager::HandlePlayerCooldownChanged(float NormalizedValue)
{
    UpdateCooldown(NormalizedValue);
}

void ASBHUDManager::HandleSystemDirectiveChanged(const FSBSystemDirective& Directive)
{
    if (Directive.Text.IsEmpty())
    {
        return;
    }
    
    if (PlayerHUDWidget)
    {
        PlayerHUDWidget->UpdateDirectiveText(Directive.Text);
    }
    
    ShowDirective(Directive.Text, 4.0f);
}

void ASBHUDManager::HandleContractChanged(const FSBContractState& ContractState)
{
    if (!PlayerHUDWidget)
    {
        return;
    }

    FString Status;
    if (ContractState.Type == ESBContractType::None)
    {
        Status = TEXT("No active contract");
    }
    else if (ContractState.bSucceeded)
    {
        Status = TEXT("Contract complete!");
    }
    else if (ContractState.bFailed)
    {
        Status = TEXT("Contract failed.");
    }
    else if (ContractState.bActive)
    {
        Status = FString::Printf(TEXT("Contract: %d/%d (%.1fs)"), 
            ContractState.ProgressCount, 
            ContractState.TargetCount,
            FMath::Max(0.0f, ContractState.TimeLimitSeconds - ContractState.ElapsedSeconds));
    }
    else
    {
        Status = TEXT("Contract offered...");
    }

    PlayerHUDWidget->UpdateContractText(Status);
}
