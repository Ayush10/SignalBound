#include "SignalBoundModule.h"
#include "Modules/ModuleManager.h"

#define LOCTEXT_NAMESPACE "FSignalBoundModule"

void FSignalBoundModule::StartupModule()
{
}

void FSignalBoundModule::ShutdownModule()
{
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FSignalBoundModule, SignalBound)
