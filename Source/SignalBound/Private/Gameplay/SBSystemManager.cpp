#include "Gameplay/SBSystemManager.h"

ASBSystemManager::ASBSystemManager()
{
    PrimaryActorTick.bCanEverTick = false;

    // Initialize Scripted Directives with ElevenLabs Audio
    FSBSystemDirective D1;
    D1.DirectiveId = TEXT("Awakening");
    D1.Text = TEXT("Citadel Zero-One status: Active. Neural link established. Awaiting Signal-bound unit for immediate deployment.");
    D1.AudioFilePath = TEXT("Saved/SystemCache/Voice/system_awakening.mp3");
    D1.ContextTag = TEXT("Hub");
    ScriptedDirectives.Add(D1);

    FSBSystemDirective D2;
    D2.DirectiveId = TEXT("WorldIntro");
    D2.Text = TEXT("Welcome to the Iron-catacombs. A world governed by the System, where every action is monitored, and every failure is logged.");
    D2.AudioFilePath = TEXT("Saved/SystemCache/Voice/world_intro.mp3");
    D2.ContextTag = TEXT("Hub");
    ScriptedDirectives.Add(D2);

    FSBSystemDirective D3;
    D3.DirectiveId = TEXT("DirectiveAlpha");
    D3.Text = TEXT("Directive Alpha-Nine: Initiate descent. Purge the catacombs of unauthorized entities. Compliance is mandatory.");
    D3.AudioFilePath = TEXT("Saved/SystemCache/Voice/gameplay_directive.mp3");
    D3.ContextTag = TEXT("Hub");
    ScriptedDirectives.Add(D3);

    FSBSystemDirective D4;
    D4.DirectiveId = TEXT("DungeonEntry");
    D4.Text = TEXT("The Ironcatacomb awaits. Steel yourself before the descent.");
    D4.ContextTag = TEXT("Floor01");
    ScriptedDirectives.Add(D4);
}

FSBSystemDirective ASBSystemManager::RequestDirective(const FString& ContextTag)
{
    FSBSystemDirective Directive;

    switch (ProviderMode)
    {
    case ESBSystemProviderMode::Scripted:
        Directive = GetScriptedDirective(ContextTag);
        break;
    case ESBSystemProviderMode::Cached:
        if (CachedDirectives.Num() > 0)
        {
            Directive = CachedDirectives[0];
            CachedDirectives.RemoveAt(0);
        }
        else
        {
            Directive = BuildFallbackDirective(ContextTag);
        }
        break;
    case ESBSystemProviderMode::LiveStub:
        // Signal the external AI service that we need a fresh directive
        bRequestPending = true;
        PendingContextTag = ContextTag;
        
        // Return a temporary stub while the service works
        Directive = BuildLiveStubDirective(ContextTag);
        break;
    default:
        Directive = BuildFallbackDirective(ContextTag);
        break;
    }

    ShowDirective(Directive);
    return Directive;
}

void ASBSystemManager::SetDirective(const FSBSystemDirective& Directive)
{
    ShowDirective(Directive);
}

void ASBSystemManager::AddCachedDirective(const FSBSystemDirective& Directive)
{
    CachedDirectives.Add(Directive);
}

void ASBSystemManager::LoadCachedDirectives(const FString& JsonContent)
{
    // Simple manual parsing or placeholder for external data injection
    // In a real project, we'd use TJsonReader
    CachedDirectives.Empty();
}

FSBSystemDirective ASBSystemManager::GetScriptedDirective(const FString& ContextTag) const
{
    if (ScriptedDirectives.IsValidIndex(ScriptedIndex))
    {
        return ScriptedDirectives[ScriptedIndex];
    }

    for (const FSBSystemDirective& Directive : ScriptedDirectives)
    {
        if (Directive.ContextTag == ContextTag)
        {
            return Directive;
        }
    }

    return BuildFallbackDirective(ContextTag);
}

void ASBSystemManager::ShowDirective(const FSBSystemDirective& Directive)
{
    CurrentDirective = Directive;
    DirectiveHistory.Add(Directive);
    OnDirectiveChanged.Broadcast(CurrentDirective);

    if (!CurrentDirective.AudioFilePath.IsEmpty())
    {
        PlayDirectiveAudio(CurrentDirective.AudioFilePath);
    }

    if (ProviderMode == ESBSystemProviderMode::Scripted && ScriptedDirectives.IsValidIndex(ScriptedIndex))
    {
        ScriptedIndex = (ScriptedIndex + 1) % FMath::Max(1, ScriptedDirectives.Num());
    }
}

void ASBSystemManager::ClearDirective()
{
    CurrentDirective = FSBSystemDirective();
    OnDirectiveChanged.Broadcast(CurrentDirective);
}

FSBSystemDirective ASBSystemManager::BuildFallbackDirective(const FString& ContextTag) const
{
    FSBSystemDirective Directive;
    Directive.DirectiveId = TEXT("Fallback");
    Directive.ContextTag = ContextTag;
    Directive.Text = TEXT("Proceed to the next objective marker.");
    Directive.TimestampUtc = FDateTime::UtcNow().ToIso8601();
    return Directive;
}

FSBSystemDirective ASBSystemManager::BuildLiveStubDirective(const FString& ContextTag) const
{
    FSBSystemDirective Directive;
    Directive.DirectiveId = TEXT("LiveStub");
    Directive.ContextTag = ContextTag;
    Directive.Text = FString::Printf(TEXT("System directive prepared for context: %s"), *ContextTag);
    Directive.TimestampUtc = FDateTime::UtcNow().ToIso8601();
    return Directive;
}
