#include "Gameplay/SBSystemManager.h"

ASBSystemManager::ASBSystemManager()
{
    PrimaryActorTick.bCanEverTick = false;

    // Initialize Scripted Directives
    FSBSystemDirective D1;
    D1.DirectiveId = TEXT("Intro");
    D1.Text = TEXT("The Citadel remembers those who fall. Rise again, Signalbound.");
    D1.ContextTag = TEXT("Hub");
    ScriptedDirectives.Add(D1);

    FSBSystemDirective D2;
    D2.DirectiveId = TEXT("ContractHint");
    D2.Text = TEXT("Contracts forge resolve. Accept the challenge, reap the signal.");
    D2.ContextTag = TEXT("Hub");
    ScriptedDirectives.Add(D2);

    FSBSystemDirective D3;
    D3.DirectiveId = TEXT("DungeonEntry");
    D3.Text = TEXT("The Ironcatacomb awaits. Steel yourself before the descent.");
    D3.ContextTag = TEXT("Floor01");
    ScriptedDirectives.Add(D3);

    FSBSystemDirective D4;
    D4.DirectiveId = TEXT("ObjectiveHint");
    D4.Text = TEXT("Three sigils seal the gate. Gather them from the depths.");
    D4.ContextTag = TEXT("Floor01");
    ScriptedDirectives.Add(D4);

    FSBSystemDirective D5;
    D5.DirectiveId = TEXT("SystemWarning");
    D5.Text = TEXT("The System watches. Every action carries weight.");
    D5.ContextTag = TEXT("General");
    ScriptedDirectives.Add(D5);
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
        // In LiveStub mode, we expect an external tool to call SetDirective
        // If not set recently, return fallback
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
