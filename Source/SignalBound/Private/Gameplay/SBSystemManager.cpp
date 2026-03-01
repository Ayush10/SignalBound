#include "Gameplay/SBSystemManager.h"

ASBSystemManager::ASBSystemManager()
{
    PrimaryActorTick.bCanEverTick = false;
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
        if (CachedDirectives.IsValidIndex(0))
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
        Directive = BuildLiveStubDirective(ContextTag);
        break;
    default:
        Directive = BuildFallbackDirective(ContextTag);
        break;
    }

    ShowDirective(Directive);
    return Directive;
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
