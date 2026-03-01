param(
    [Parameter(Mandatory = $true)]
    [string]$Command,

    [Parameter(Mandatory = $false)]
    [string]$Params = "{}"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $env:UNREAL_MCP_PY_DIR) {
    throw "UNREAL_MCP_PY_DIR is not set. Point it to <path>\unreal-engine-mcp\Python."
}

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    throw "uv is not installed or not in PATH."
}

& $uvCmd.Source --directory $env:UNREAL_MCP_PY_DIR run python "$ScriptDir/unreal_mcp_exec.py" $Command $Params

