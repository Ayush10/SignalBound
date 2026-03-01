using UnrealBuildTool;

public class SignalBoundEditorTarget : TargetRules
{
	public SignalBoundEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("SignalBound");
	}
}
