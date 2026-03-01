#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "SBEnemySpawnMarker.generated.h"

class UArrowComponent;

UCLASS(Blueprintable)
class SIGNALBOUND_API ASBEnemySpawnMarker : public AActor
{
    GENERATED_BODY()

public:
    ASBEnemySpawnMarker();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn")
    FName SpawnGroupTag = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn")
    int32 FloorNumber = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn")
    int32 RoomNumber = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn")
    bool bIsEliteSpawn = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Spawn")
    bool bIsBossSpawn = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
    UArrowComponent* Arrow = nullptr;
};
