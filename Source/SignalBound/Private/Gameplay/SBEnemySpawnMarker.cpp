#include "Gameplay/SBEnemySpawnMarker.h"

#include "Components/ArrowComponent.h"

ASBEnemySpawnMarker::ASBEnemySpawnMarker()
{
    PrimaryActorTick.bCanEverTick = false;
    Arrow = CreateDefaultSubobject<UArrowComponent>(TEXT("Arrow"));
    RootComponent = Arrow;
}
