#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Gameplay/SBGameplayTypes.h"
#include "SBHUDManager.generated.h"

class USBWidget_PlayerHUD;
class USBWidget_SystemNotice;
class USBWidget_SystemMenu;
class APlayerController;
class ASBPlayerCharacter;
class ASBSystemManager;
class ASBContractManager;

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBHUDManager : public AActor
{
    GENERATED_BODY()

public:
    ASBHUDManager();

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void CreateHUD(APlayerController* ForPlayerController);

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void UpdateHealth(float NormalizedValue);

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void UpdateStamina(float NormalizedValue);

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void UpdateCooldown(float NormalizedValue);

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void ShowNotice(const FString& Text, float Duration = 3.0f);

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void ShowDirective(const FString& Text, float Duration = 4.0f);

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void ToggleMenu();

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void BindToPlayer(ASBPlayerCharacter* InPlayerCharacter);

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void BindToSystemManager(ASBSystemManager* InSystemManager);

    UFUNCTION(BlueprintCallable, Category = "HUD")
    void BindToContractManager(ASBContractManager* InContractManager);

    UFUNCTION(BlueprintPure, Category = "HUD")
    USBWidget_PlayerHUD* GetPlayerHUD() const { return PlayerHUDWidget; }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
    TSubclassOf<USBWidget_PlayerHUD> PlayerHUDClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
    TSubclassOf<USBWidget_SystemNotice> SystemNoticeClass;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
    TSubclassOf<USBWidget_SystemMenu> SystemMenuClass;

private:
    UFUNCTION()
    void HandlePlayerHealthChanged(float NormalizedValue);

    UFUNCTION()
    void HandlePlayerStaminaChanged(float NormalizedValue);

    UFUNCTION()
    void HandlePlayerCooldownChanged(float NormalizedValue);

    UFUNCTION()
    void HandleSystemDirectiveChanged(const FSBSystemDirective& Directive);

    UFUNCTION()
    void HandleContractChanged(const FSBContractState& ContractState);

    UPROPERTY(Transient)
    USBWidget_PlayerHUD* PlayerHUDWidget = nullptr;

    UPROPERTY(Transient)
    USBWidget_SystemNotice* SystemNoticeWidget = nullptr;

    UPROPERTY(Transient)
    USBWidget_SystemMenu* SystemMenuWidget = nullptr;

    UPROPERTY(Transient)
    ASBPlayerCharacter* BoundPlayerCharacter = nullptr;

    UPROPERTY(Transient)
    ASBSystemManager* BoundSystemManager = nullptr;

    UPROPERTY(Transient)
    ASBContractManager* BoundContractManager = nullptr;
};
