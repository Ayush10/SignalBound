#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Gameplay/SBGameplayTypes.h"
#include "SBSystemManager.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FSBDirectiveChangedSignature, const FSBSystemDirective&, Directive);

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBSystemManager : public AActor
{
    GENERATED_BODY()

public:
    ASBSystemManager();

    UFUNCTION(BlueprintCallable, Category = "System")
    FSBSystemDirective RequestDirective(const FString& ContextTag);

    UFUNCTION(BlueprintCallable, Category = "System")
    void SetDirective(const FSBSystemDirective& Directive);

    UFUNCTION(BlueprintCallable, Category = "System")
    void LoadCachedDirectives(const FString& JsonContent);

    UFUNCTION(BlueprintCallable, Category = "System")
    void AddCachedDirective(const FSBSystemDirective& Directive);

    UFUNCTION(BlueprintPure, Category = "System")
    FSBSystemDirective GetScriptedDirective(const FString& ContextTag) const;

    UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "System")
    bool bRequestPending = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "System")
    FString PendingContextTag;

    UFUNCTION(BlueprintCallable, Category = "System")
    void ShowDirective(const FSBSystemDirective& Directive);

    UFUNCTION(BlueprintCallable, Category = "System")
    void ClearDirective();

    UFUNCTION(BlueprintPure, Category = "System")
    FSBSystemDirective GetCurrentDirective() const { return CurrentDirective; }

    UFUNCTION(BlueprintCallable, Category = "System")
    void SetProviderMode(ESBSystemProviderMode InProviderMode) { ProviderMode = InProviderMode; }

    UFUNCTION(BlueprintPure, Category = "System")
    ESBSystemProviderMode GetProviderMode() const { return ProviderMode; }

    UPROPERTY(BlueprintAssignable, Category = "Events")
    FSBDirectiveChangedSignature OnDirectiveChanged;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "System")
    ESBSystemProviderMode ProviderMode = ESBSystemProviderMode::Scripted;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "System")
    TArray<FSBSystemDirective> ScriptedDirectives;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "System")
    TArray<FSBSystemDirective> CachedDirectives;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "System")
    TArray<FSBSystemDirective> DirectiveHistory;

private:
    FSBSystemDirective BuildFallbackDirective(const FString& ContextTag) const;
    FSBSystemDirective BuildLiveStubDirective(const FString& ContextTag) const;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "System", meta = (AllowPrivateAccess = "true"))
    FSBSystemDirective CurrentDirective;

    int32 ScriptedIndex = 0;
};
