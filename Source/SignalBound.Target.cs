using UnrealBuildTool;

public class SignalBoundTarget : TargetRules
{
	public SignalBoundTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("SignalBound");
	}
}
