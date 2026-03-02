#include "Commands/EpicUnrealMCPEditorCommands.h"
#include "Commands/EpicUnrealMCPCommonUtils.h"
#include "Editor.h"
#include "EditorViewportClient.h"
#include "LevelEditorViewport.h"
#include "ImageUtils.h"
#include "HighResScreenshot.h"
#include "Engine/GameViewportClient.h"
#include "Misc/FileHelper.h"
#include "FileHelpers.h"
#include "Misc/PackageName.h"
#include "GameFramework/Actor.h"
#include "Engine/Selection.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/Light.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PointLight.h"
#include "Engine/SpotLight.h"
#include "Camera/CameraActor.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/LightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/TextRenderComponent.h"
#include "EditorSubsystem.h"
#include "Subsystems/EditorActorSubsystem.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "EditorAssetLibrary.h"
#include "Commands/EpicUnrealMCPBlueprintCommands.h"
#include "UObject/UnrealType.h"
#include "GameFramework/WorldSettings.h"
#include "GameFramework/GameModeBase.h"

namespace
{
AActor* FindActorByNameExact(UWorld* World, const FString& ActorName)
{
    if (!World)
    {
        return nullptr;
    }

    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(World, AActor::StaticClass(), AllActors);

    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            return Actor;
        }
    }

    return nullptr;
}

bool SetIntPropertyByName(UObject* Object, const FName PropertyName, int32 Value)
{
    if (!Object)
    {
        return false;
    }

    if (FIntProperty* IntProp = CastField<FIntProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
    {
        IntProp->SetPropertyValue_InContainer(Object, Value);
        return true;
    }

    return false;
}

bool SetFloatPropertyByName(UObject* Object, const FName PropertyName, float Value)
{
    if (!Object)
    {
        return false;
    }

    if (FFloatProperty* FloatProp = CastField<FFloatProperty>(Object->GetClass()->FindPropertyByName(PropertyName)))
    {
        FloatProp->SetPropertyValue_InContainer(Object, Value);
        return true;
    }

    return false;
}
} // namespace

FEpicUnrealMCPEditorCommands::FEpicUnrealMCPEditorCommands()
{
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
    // Actor manipulation commands
    if (CommandType == TEXT("get_actors_in_level"))
    {
        return HandleGetActorsInLevel(Params);
    }
    else if (CommandType == TEXT("find_actors_by_name"))
    {
        return HandleFindActorsByName(Params);
    }
    else if (CommandType == TEXT("spawn_actor"))
    {
        return HandleSpawnActor(Params);
    }
    else if (CommandType == TEXT("delete_actor"))
    {
        return HandleDeleteActor(Params);
    }
    else if (CommandType == TEXT("set_actor_transform"))
    {
        return HandleSetActorTransform(Params);
    }
    else if (CommandType == TEXT("set_actor_tags"))
    {
        return HandleSetActorTags(Params);
    }
    else if (CommandType == TEXT("set_actor_label"))
    {
        return HandleSetActorLabel(Params);
    }
    else if (CommandType == TEXT("set_light_properties"))
    {
        return HandleSetLightProperties(Params);
    }
    else if (CommandType == TEXT("add_text_render_component"))
    {
        return HandleAddTextRenderComponent(Params);
    }
    else if (CommandType == TEXT("save_current_level"))
    {
        return HandleSaveCurrentLevel(Params);
    }
    else if (CommandType == TEXT("save_current_level_as"))
    {
        return HandleSaveCurrentLevelAs(Params);
    }
    else if (CommandType == TEXT("load_level"))
    {
        return HandleLoadLevel(Params);
    }
    else if (CommandType == TEXT("new_blank_level"))
    {
        return HandleNewBlankLevel(Params);
    }
    // Blueprint actor spawning
    else if (CommandType == TEXT("spawn_blueprint_actor"))
    {
        return HandleSpawnBlueprintActor(Params);
    }
    // World settings
    else if (CommandType == TEXT("set_world_settings"))
    {
        return HandleSetWorldSettings(Params);
    }
    else if (CommandType == TEXT("get_world_settings"))
    {
        return HandleGetWorldSettings(Params);
    }

    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown editor command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleGetActorsInLevel(const TSharedPtr<FJsonObject>& Params)
{
    FString ActorTypeFilter;
    Params->TryGetStringField(TEXT("actor_type"), ActorTypeFilter);

    FString NameContainsFilter;
    Params->TryGetStringField(TEXT("name_contains"), NameContainsFilter);

    int32 MaxResults = 0;
    Params->TryGetNumberField(TEXT("max_results"), MaxResults);

    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    TArray<TSharedPtr<FJsonValue>> ActorArray;
    int32 TotalMatching = 0;
    for (AActor* Actor : AllActors)
    {
        if (!Actor)
        {
            continue;
        }

        if (!ActorTypeFilter.IsEmpty() && Actor->GetClass()->GetName() != ActorTypeFilter)
        {
            continue;
        }

        if (!NameContainsFilter.IsEmpty() && !Actor->GetName().Contains(NameContainsFilter))
        {
            continue;
        }

        ++TotalMatching;
        if (MaxResults <= 0 || ActorArray.Num() < MaxResults)
        {
            ActorArray.Add(FEpicUnrealMCPCommonUtils::ActorToJson(Actor));
        }
    }
    
    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetArrayField(TEXT("actors"), ActorArray);
    ResultObj->SetNumberField(TEXT("matching_count"), TotalMatching);
    ResultObj->SetNumberField(TEXT("returned_count"), ActorArray.Num());
    
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleFindActorsByName(const TSharedPtr<FJsonObject>& Params)
{
    FString Pattern;
    if (!Params->TryGetStringField(TEXT("pattern"), Pattern))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'pattern' parameter"));
    }
    
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    TArray<TSharedPtr<FJsonValue>> MatchingActors;
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName().Contains(Pattern))
        {
            MatchingActors.Add(FEpicUnrealMCPCommonUtils::ActorToJson(Actor));
        }
    }
    
    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetArrayField(TEXT("actors"), MatchingActors);
    
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSpawnActor(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString ActorType;
    if (!Params->TryGetStringField(TEXT("type"), ActorType))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'type' parameter"));
    }

    // Get actor name (required parameter)
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    // Get optional transform parameters
    FVector Location(0.0f, 0.0f, 0.0f);
    FRotator Rotation(0.0f, 0.0f, 0.0f);
    FVector Scale(1.0f, 1.0f, 1.0f);

    if (Params->HasField(TEXT("location")))
    {
        Location = FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location"));
    }
    if (Params->HasField(TEXT("rotation")))
    {
        Rotation = FEpicUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation"));
    }
    if (Params->HasField(TEXT("scale")))
    {
        Scale = FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale"));
    }

    // Create the actor based on type
    AActor* NewActor = nullptr;
    UWorld* World = GEditor->GetEditorWorldContext().World();

    if (!World)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get editor world"));
    }

    // Check if an actor with this name already exists
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(World, AActor::StaticClass(), AllActors);
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor with name '%s' already exists"), *ActorName));
        }
    }

    FActorSpawnParameters SpawnParams;
    SpawnParams.Name = *ActorName;

    if (ActorType == TEXT("StaticMeshActor"))
    {
        AStaticMeshActor* NewMeshActor = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), Location, Rotation, SpawnParams);
        if (NewMeshActor)
        {
            // Check for an optional static_mesh parameter to assign a mesh
            FString MeshPath;
            if (Params->TryGetStringField(TEXT("static_mesh"), MeshPath))
            {
                UStaticMesh* Mesh = Cast<UStaticMesh>(UEditorAssetLibrary::LoadAsset(MeshPath));
                if (Mesh)
                {
                    NewMeshActor->GetStaticMeshComponent()->SetStaticMesh(Mesh);
                }
                else
                {
                    UE_LOG(LogTemp, Warning, TEXT("Could not find static mesh at path: %s"), *MeshPath);
                }
            }
        }
        NewActor = NewMeshActor;
    }
    else if (ActorType == TEXT("PointLight"))
    {
        NewActor = World->SpawnActor<APointLight>(APointLight::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("SpotLight"))
    {
        NewActor = World->SpawnActor<ASpotLight>(ASpotLight::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("DirectionalLight"))
    {
        NewActor = World->SpawnActor<ADirectionalLight>(ADirectionalLight::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("CameraActor"))
    {
        NewActor = World->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), Location, Rotation, SpawnParams);
    }
    else
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown actor type: %s"), *ActorType));
    }

    if (NewActor)
    {
        // Set scale (since SpawnActor only takes location and rotation)
        FTransform Transform = NewActor->GetTransform();
        Transform.SetScale3D(Scale);
        NewActor->SetActorTransform(Transform);

        // Return the created actor's details
        return FEpicUnrealMCPCommonUtils::ActorToJsonObject(NewActor, true);
    }

    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create actor"));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleDeleteActor(const TSharedPtr<FJsonObject>& Params)
{
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            // Store actor info before deletion for the response
            TSharedPtr<FJsonObject> ActorInfo = FEpicUnrealMCPCommonUtils::ActorToJsonObject(Actor);
            
            // Delete the actor
            Actor->Destroy();
            
            TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
            ResultObj->SetObjectField(TEXT("deleted_actor"), ActorInfo);
            return ResultObj;
        }
    }
    
    return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSetActorTransform(const TSharedPtr<FJsonObject>& Params)
{
    // Get actor name
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    // Find the actor
    AActor* TargetActor = nullptr;
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            TargetActor = Actor;
            break;
        }
    }

    if (!TargetActor)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    // Get transform parameters
    FTransform NewTransform = TargetActor->GetTransform();

    if (Params->HasField(TEXT("location")))
    {
        NewTransform.SetLocation(FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location")));
    }
    if (Params->HasField(TEXT("rotation")))
    {
        NewTransform.SetRotation(FQuat(FEpicUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation"))));
    }
    if (Params->HasField(TEXT("scale")))
    {
        NewTransform.SetScale3D(FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale")));
    }

    // Set the new transform
    TargetActor->SetActorTransform(NewTransform);

    // Return updated actor info
    return FEpicUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true);
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSetActorTags(const TSharedPtr<FJsonObject>& Params)
{
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    const TArray<TSharedPtr<FJsonValue>>* TagValues = nullptr;
    if (!Params->TryGetArrayField(TEXT("tags"), TagValues) || !TagValues)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing or invalid 'tags' array parameter"));
    }

    const bool bAppend = Params->HasField(TEXT("append")) ? Params->GetBoolField(TEXT("append")) : false;

    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    AActor* TargetActor = FindActorByNameExact(World ? World : GWorld, ActorName);
    if (!TargetActor)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    TargetActor->Modify();
    if (!bAppend)
    {
        TargetActor->Tags.Empty();
    }

    for (const TSharedPtr<FJsonValue>& TagValue : *TagValues)
    {
        FString TagString;
        if (!TagValue.IsValid() || !TagValue->TryGetString(TagString))
        {
            return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("All 'tags' entries must be strings"));
        }

        TagString.TrimStartAndEndInline();
        if (!TagString.IsEmpty())
        {
            TargetActor->Tags.AddUnique(FName(*TagString));
        }
    }

    TargetActor->MarkPackageDirty();

    TSharedPtr<FJsonObject> ResultObj = FEpicUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true);
    TArray<TSharedPtr<FJsonValue>> TagsJson;
    for (const FName& Tag : TargetActor->Tags)
    {
        TagsJson.Add(MakeShared<FJsonValueString>(Tag.ToString()));
    }
    ResultObj->SetArrayField(TEXT("tags"), TagsJson);
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSetActorLabel(const TSharedPtr<FJsonObject>& Params)
{
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    FString Label;
    if (!Params->TryGetStringField(TEXT("label"), Label))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'label' parameter"));
    }

    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    AActor* TargetActor = FindActorByNameExact(World ? World : GWorld, ActorName);
    if (!TargetActor)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    TargetActor->Modify();
#if WITH_EDITOR
    TargetActor->SetActorLabel(Label, true);
#endif
    TargetActor->MarkPackageDirty();

    TSharedPtr<FJsonObject> ResultObj = FEpicUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true);
    ResultObj->SetStringField(TEXT("label"), Label);
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSetLightProperties(const TSharedPtr<FJsonObject>& Params)
{
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    AActor* TargetActor = FindActorByNameExact(World ? World : GWorld, ActorName);
    if (!TargetActor)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    ALight* LightActor = Cast<ALight>(TargetActor);
    if (!LightActor || !LightActor->GetLightComponent())
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Target actor is not a light actor"));
    }

    ULightComponent* LightComponent = LightActor->GetLightComponent();
    bool bChanged = false;

    if (Params->HasField(TEXT("intensity")))
    {
        LightComponent->SetIntensity(static_cast<float>(Params->GetNumberField(TEXT("intensity"))));
        bChanged = true;
    }

    if (Params->HasField(TEXT("cast_shadows")))
    {
        LightComponent->SetCastShadows(Params->GetBoolField(TEXT("cast_shadows")));
        bChanged = true;
    }

    if (Params->HasField(TEXT("indirect_lighting_intensity")))
    {
        LightComponent->SetIndirectLightingIntensity(static_cast<float>(Params->GetNumberField(TEXT("indirect_lighting_intensity"))));
        bChanged = true;
    }

    if (Params->HasField(TEXT("use_temperature")))
    {
        LightComponent->SetUseTemperature(Params->GetBoolField(TEXT("use_temperature")));
        bChanged = true;
    }

    if (Params->HasField(TEXT("temperature")))
    {
        LightComponent->SetTemperature(static_cast<float>(Params->GetNumberField(TEXT("temperature"))));
        bChanged = true;
    }

    const TArray<TSharedPtr<FJsonValue>>* ColorArray = nullptr;
    if (Params->TryGetArrayField(TEXT("light_color"), ColorArray) && ColorArray && ColorArray->Num() >= 3)
    {
        const float R = static_cast<float>((*ColorArray)[0]->AsNumber());
        const float G = static_cast<float>((*ColorArray)[1]->AsNumber());
        const float B = static_cast<float>((*ColorArray)[2]->AsNumber());
        LightComponent->SetLightColor(FLinearColor(R, G, B), true);
        bChanged = true;
    }

    if (Params->HasField(TEXT("forward_shading_priority")))
    {
        const int32 Priority = static_cast<int32>(Params->GetNumberField(TEXT("forward_shading_priority")));
        if (!SetIntPropertyByName(LightComponent, TEXT("ForwardShadingPriority"), Priority))
        {
            return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to set ForwardShadingPriority on light component"));
        }
        bChanged = true;
    }

    if (Params->HasField(TEXT("attenuation_radius")))
    {
        if (UPointLightComponent* PointLight = Cast<UPointLightComponent>(LightComponent))
        {
            PointLight->SetAttenuationRadius(static_cast<float>(Params->GetNumberField(TEXT("attenuation_radius"))));
            bChanged = true;
        }
    }

    if (Params->HasField(TEXT("inner_cone_angle")))
    {
        if (USpotLightComponent* SpotLight = Cast<USpotLightComponent>(LightComponent))
        {
            SpotLight->SetInnerConeAngle(static_cast<float>(Params->GetNumberField(TEXT("inner_cone_angle"))));
            bChanged = true;
        }
    }

    if (Params->HasField(TEXT("outer_cone_angle")))
    {
        if (USpotLightComponent* SpotLight = Cast<USpotLightComponent>(LightComponent))
        {
            SpotLight->SetOuterConeAngle(static_cast<float>(Params->GetNumberField(TEXT("outer_cone_angle"))));
            bChanged = true;
        }
    }

    if (Params->HasField(TEXT("source_angle")))
    {
        if (UDirectionalLightComponent* Directional = Cast<UDirectionalLightComponent>(LightComponent))
        {
            if (!SetFloatPropertyByName(Directional, TEXT("SourceAngle"), static_cast<float>(Params->GetNumberField(TEXT("source_angle")))))
            {
                return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to set SourceAngle on directional light"));
            }
            bChanged = true;
        }
    }

    if (bChanged)
    {
        LightActor->Modify();
        LightActor->MarkPackageDirty();
        LightComponent->MarkRenderStateDirty();
    }

    TSharedPtr<FJsonObject> ResultObj = FEpicUnrealMCPCommonUtils::ActorToJsonObject(LightActor, true);
    ResultObj->SetBoolField(TEXT("updated"), bChanged);
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleAddTextRenderComponent(const TSharedPtr<FJsonObject>& Params)
{
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    FString ComponentName;
    if (!Params->TryGetStringField(TEXT("component_name"), ComponentName))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'component_name' parameter"));
    }

    FString Text;
    if (!Params->TryGetStringField(TEXT("text"), Text))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'text' parameter"));
    }

    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
    AActor* TargetActor = FindActorByNameExact(World ? World : GWorld, ActorName);
    if (!TargetActor)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    for (UActorComponent* ExistingComponent : TargetActor->GetComponents())
    {
        if (ExistingComponent && ExistingComponent->GetName() == ComponentName)
        {
            return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Component already exists: %s"), *ComponentName));
        }
    }

    USceneComponent* RootComponent = TargetActor->GetRootComponent();
    if (!RootComponent)
    {
        RootComponent = NewObject<USceneComponent>(TargetActor, USceneComponent::StaticClass(), TEXT("RootComponent"), RF_Transactional);
        if (!RootComponent)
        {
            return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create root component"));
        }
        TargetActor->SetRootComponent(RootComponent);
        RootComponent->RegisterComponent();
    }

    UTextRenderComponent* TextComponent = NewObject<UTextRenderComponent>(TargetActor, UTextRenderComponent::StaticClass(), *ComponentName, RF_Transactional);
    if (!TextComponent)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create TextRenderComponent"));
    }

    TargetActor->Modify();
    TargetActor->AddInstanceComponent(TextComponent);
    TextComponent->SetupAttachment(RootComponent);
    TextComponent->SetText(FText::FromString(Text));

    if (Params->HasField(TEXT("location")))
    {
        TextComponent->SetRelativeLocation(FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location")));
    }
    if (Params->HasField(TEXT("rotation")))
    {
        TextComponent->SetRelativeRotation(FEpicUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation")));
    }
    if (Params->HasField(TEXT("scale")))
    {
        TextComponent->SetRelativeScale3D(FEpicUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale")));
    }

    if (Params->HasField(TEXT("world_size")))
    {
        TextComponent->SetWorldSize(static_cast<float>(Params->GetNumberField(TEXT("world_size"))));
    }

    const TArray<TSharedPtr<FJsonValue>>* TextColorArray = nullptr;
    if (Params->TryGetArrayField(TEXT("text_color"), TextColorArray) && TextColorArray && TextColorArray->Num() >= 3)
    {
        float R = static_cast<float>((*TextColorArray)[0]->AsNumber());
        float G = static_cast<float>((*TextColorArray)[1]->AsNumber());
        float B = static_cast<float>((*TextColorArray)[2]->AsNumber());
        float A = TextColorArray->Num() >= 4 ? static_cast<float>((*TextColorArray)[3]->AsNumber()) : 1.0f;

        if (R <= 1.0f && G <= 1.0f && B <= 1.0f && A <= 1.0f)
        {
            R *= 255.0f;
            G *= 255.0f;
            B *= 255.0f;
            A *= 255.0f;
        }

        TextComponent->SetTextRenderColor(FColor(
            static_cast<uint8>(FMath::Clamp(R, 0.0f, 255.0f)),
            static_cast<uint8>(FMath::Clamp(G, 0.0f, 255.0f)),
            static_cast<uint8>(FMath::Clamp(B, 0.0f, 255.0f)),
            static_cast<uint8>(FMath::Clamp(A, 0.0f, 255.0f))
        ));
    }

    TextComponent->RegisterComponent();
    TargetActor->MarkPackageDirty();

    TSharedPtr<FJsonObject> ResultObj = FEpicUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true);
    ResultObj->SetStringField(TEXT("component_name"), TextComponent->GetName());
    ResultObj->SetStringField(TEXT("text"), Text);
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSaveCurrentLevel(const TSharedPtr<FJsonObject>& Params)
{
    const bool bSaved = FEditorFileUtils::SaveCurrentLevel();
    if (!bSaved)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to save current level"));
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetBoolField(TEXT("saved"), true);
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSaveCurrentLevelAs(const TSharedPtr<FJsonObject>& Params)
{
    FString MapPath;
    if (!Params->TryGetStringField(TEXT("map_path"), MapPath))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'map_path' parameter"));
    }

    UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : GWorld;
    if (!World || !World->PersistentLevel)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No current persistent level to save"));
    }

    FString TargetFilename = MapPath;
    if (MapPath.StartsWith(TEXT("/")))
    {
        TargetFilename = FPackageName::LongPackageNameToFilename(MapPath, FPackageName::GetMapPackageExtension());
    }

    FString SavedFilename;
    const bool bSaved = FEditorFileUtils::SaveLevel(World->PersistentLevel, TargetFilename, &SavedFilename);
    if (!bSaved)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to save level as: %s"), *MapPath));
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetBoolField(TEXT("saved"), true);
    ResultObj->SetStringField(TEXT("saved_filename"), SavedFilename);
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleLoadLevel(const TSharedPtr<FJsonObject>& Params)
{
    FString MapPath;
    if (!Params->TryGetStringField(TEXT("map_path"), MapPath))
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'map_path' parameter"));
    }

    FString Filename = MapPath;
    if (MapPath.StartsWith(TEXT("/")))
    {
        Filename = FPackageName::LongPackageNameToFilename(MapPath, FPackageName::GetMapPackageExtension());
    }

    UWorld* LoadedWorld = UEditorLoadingAndSavingUtils::LoadMap(Filename);
    if (!LoadedWorld)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to load level: %s"), *MapPath));
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetBoolField(TEXT("loaded"), true);
    ResultObj->SetStringField(TEXT("world_name"), LoadedWorld->GetName());
    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleNewBlankLevel(const TSharedPtr<FJsonObject>& Params)
{
    const bool bSaveExisting = Params->HasField(TEXT("save_existing")) ? Params->GetBoolField(TEXT("save_existing")) : false;

    UWorld* NewWorld = UEditorLoadingAndSavingUtils::NewBlankMap(bSaveExisting);
    if (!NewWorld)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create blank level"));
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetBoolField(TEXT("created"), true);
    ResultObj->SetStringField(TEXT("world_name"), NewWorld->GetName());

    FString MapPath;
    if (Params->TryGetStringField(TEXT("map_path"), MapPath))
    {
        FString TargetFilename = MapPath;
        if (MapPath.StartsWith(TEXT("/")))
        {
            TargetFilename = FPackageName::LongPackageNameToFilename(MapPath, FPackageName::GetMapPackageExtension());
        }

        FString SavedFilename;
        const bool bSaved = FEditorFileUtils::SaveLevel(NewWorld->PersistentLevel, TargetFilename, &SavedFilename);
        ResultObj->SetBoolField(TEXT("saved"), bSaved);
        if (bSaved)
        {
            ResultObj->SetStringField(TEXT("saved_filename"), SavedFilename);
        }
        else
        {
            ResultObj->SetStringField(TEXT("save_error"), FString::Printf(TEXT("Could not save new level to: %s"), *MapPath));
        }
    }

    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSpawnBlueprintActor(const TSharedPtr<FJsonObject>& Params)
{
    // This function will now correctly call the implementation in BlueprintCommands
    FEpicUnrealMCPBlueprintCommands BlueprintCommands;
    return BlueprintCommands.HandleCommand(TEXT("spawn_blueprint_actor"), Params);
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleSetWorldSettings(const TSharedPtr<FJsonObject>& Params)
{
    UWorld* World = GWorld;
    if (!World)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No valid world"));
    }

    AWorldSettings* WS = World->GetWorldSettings();
    if (!WS)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No WorldSettings actor"));
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShareable(new FJsonObject);
    TArray<FString> Applied;

    // GameMode override: pass class path like "/Script/SignalBound.SBSignalBoundGameMode" or "None" to clear
    FString GameModeOverride;
    if (Params->TryGetStringField(TEXT("game_mode_override"), GameModeOverride))
    {
        WS->Modify();
        if (GameModeOverride == TEXT("None") || GameModeOverride == TEXT("none") || GameModeOverride.IsEmpty())
        {
            WS->DefaultGameMode = nullptr;
            Applied.Add(TEXT("game_mode_override=None"));
        }
        else
        {
            UClass* GMClass = LoadClass<AGameModeBase>(nullptr, *GameModeOverride);
            if (!GMClass)
            {
                // Try as a Blueprint path
                FString BlueprintPath = GameModeOverride;
                if (!BlueprintPath.EndsWith(TEXT("_C")))
                {
                    BlueprintPath += TEXT("_C");
                }
                GMClass = LoadClass<AGameModeBase>(nullptr, *BlueprintPath);
            }
            if (GMClass)
            {
                WS->DefaultGameMode = GMClass;
                Applied.Add(FString::Printf(TEXT("game_mode_override=%s"), *GMClass->GetPathName()));
            }
            else
            {
                return FEpicUnrealMCPCommonUtils::CreateErrorResponse(
                    FString::Printf(TEXT("Could not load GameMode class: %s"), *GameModeOverride));
            }
        }
    }

    // Gravity
    double GravityZ;
    if (Params->TryGetNumberField(TEXT("gravity_z"), GravityZ))
    {
        WS->bGlobalGravitySet = true;
        WS->GlobalGravityZ = static_cast<float>(GravityZ);
        Applied.Add(FString::Printf(TEXT("gravity_z=%.1f"), GravityZ));
    }

    // Kill Z
    double KillZ;
    if (Params->TryGetNumberField(TEXT("kill_z"), KillZ))
    {
        WS->KillZ = static_cast<float>(KillZ);
        Applied.Add(FString::Printf(TEXT("kill_z=%.1f"), KillZ));
    }

    WS->MarkPackageDirty();

    TArray<TSharedPtr<FJsonValue>> AppliedArray;
    for (const FString& S : Applied)
    {
        AppliedArray.Add(MakeShareable(new FJsonValueString(S)));
    }
    ResultObj->SetArrayField(TEXT("applied"), AppliedArray);
    ResultObj->SetStringField(TEXT("message"), FString::Printf(TEXT("WorldSettings updated (%d properties)"), Applied.Num()));

    return ResultObj;
}

TSharedPtr<FJsonObject> FEpicUnrealMCPEditorCommands::HandleGetWorldSettings(const TSharedPtr<FJsonObject>& Params)
{
    UWorld* World = GWorld;
    if (!World)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No valid world"));
    }

    AWorldSettings* WS = World->GetWorldSettings();
    if (!WS)
    {
        return FEpicUnrealMCPCommonUtils::CreateErrorResponse(TEXT("No WorldSettings actor"));
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShareable(new FJsonObject);

    // GameMode override
    if (WS->DefaultGameMode)
    {
        ResultObj->SetStringField(TEXT("game_mode_override"), WS->DefaultGameMode->GetPathName());
    }
    else
    {
        ResultObj->SetStringField(TEXT("game_mode_override"), TEXT("None"));
    }

    // Gravity
    ResultObj->SetNumberField(TEXT("gravity_z"), WS->GlobalGravityZ);
    ResultObj->SetBoolField(TEXT("gravity_set"), WS->bGlobalGravitySet);

    // Kill Z
    ResultObj->SetNumberField(TEXT("kill_z"), WS->KillZ);

    // Map name
    ResultObj->SetStringField(TEXT("map_name"), World->GetMapName());

    return ResultObj;
}
