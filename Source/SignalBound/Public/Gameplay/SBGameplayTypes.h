#pragma once

#include "CoreMinimal.h"
#include "SBGameplayTypes.generated.h"

UENUM(BlueprintType)
enum class ESBEnemyState : uint8
{
    Idle = 0 UMETA(DisplayName = "Idle"),
    Chase = 1 UMETA(DisplayName = "Chase"),
    Windup = 2 UMETA(DisplayName = "Windup"),
    Attack = 3 UMETA(DisplayName = "Attack"),
    Recover = 4 UMETA(DisplayName = "Recover"),
    Stunned = 5 UMETA(DisplayName = "Stunned"),
    HitReact = 6 UMETA(DisplayName = "HitReact"),
    Dead = 7 UMETA(DisplayName = "Dead")
};

UENUM(BlueprintType)
enum class ESBSystemProviderMode : uint8
{
    Scripted = 0 UMETA(DisplayName = "Scripted"),
    Cached = 1 UMETA(DisplayName = "Cached"),
    LiveStub = 2 UMETA(DisplayName = "LiveStub")
};

UENUM(BlueprintType)
enum class ESBContractType : uint8
{
    None = 0 UMETA(DisplayName = "None"),
    NoHeal = 1 UMETA(DisplayName = "NoHeal"),
    ParryChain = 2 UMETA(DisplayName = "ParryChain"),
    NoHits = 3 UMETA(DisplayName = "NoHits"),
    KillCount = 4 UMETA(DisplayName = "KillCount"),
    LowHPSurvival = 5 UMETA(DisplayName = "LowHPSurvival"),
    FastClear = 6 UMETA(DisplayName = "FastClear")
};

USTRUCT(BlueprintType)
struct FSBSystemDirective
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Directive")
    FName DirectiveId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Directive")
    FString Text;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Directive")
    FString AudioFilePath;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Directive")
    FString ContextTag;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Directive")
    FString TimestampUtc;
};

USTRUCT(BlueprintType)
struct FSBContractState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contract")
    ESBContractType Type = ESBContractType::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contract")
    int32 TargetCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contract")
    float TimeLimitSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contract")
    float ElapsedSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contract")
    int32 ProgressCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contract")
    bool bActive = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contract")
    bool bSucceeded = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Contract")
    bool bFailed = false;
};
