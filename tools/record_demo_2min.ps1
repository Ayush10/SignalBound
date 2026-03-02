param(
    [string]$OutputPath = "",
    [int]$DurationSec = 120,
    [switch]$LaunchEditor,
    [string]$MapPath = "/Game/Map_HubCitadelCity"
)

$ErrorActionPreference = "Stop"

function Resolve-FFmpeg {
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if (-not $cmd) {
        throw "ffmpeg is not installed or not on PATH."
    }
    return $cmd.Source
}

function Ensure-OutputPath([string]$RequestedPath) {
    if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
        $dir = Split-Path -Parent $RequestedPath
        if (-not [string]::IsNullOrWhiteSpace($dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        return $RequestedPath
    }

    $demoDir = Join-Path $PSScriptRoot "..\Saved\Demo"
    New-Item -ItemType Directory -Path $demoDir -Force | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    return (Join-Path $demoDir ("SignalBound_Demo_{0}.mp4" -f $stamp))
}

function Maybe-LaunchEditor([string]$TargetMap) {
    $running = Get-Process UnrealEditor -ErrorAction SilentlyContinue
    if ($running) {
        Write-Host "UnrealEditor already running."
        return
    }

    $uproject = Join-Path (Resolve-Path "$PSScriptRoot\..").Path "SignalBound.uproject"
    $editorExe = "C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe"
    if (-not (Test-Path $editorExe)) {
        throw "UnrealEditor.exe not found at expected path: $editorExe"
    }
    if (-not (Test-Path $uproject)) {
        throw "SignalBound.uproject not found: $uproject"
    }

    Write-Host "Launching Unreal Editor..."
    Start-Process -FilePath $editorExe -ArgumentList "`"$uproject`" $TargetMap"
    Start-Sleep -Seconds 25
}

function Get-ScreenSize {
    Add-Type -AssemblyName System.Windows.Forms
    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    return @{
        Width = [int]$bounds.Width
        Height = [int]$bounds.Height
    }
}

$ffmpeg = Resolve-FFmpeg
$finalOutput = Ensure-OutputPath -RequestedPath $OutputPath

if ($LaunchEditor) {
    Maybe-LaunchEditor -TargetMap $MapPath
}

$size = Get-ScreenSize
Write-Host ("Recording {0} seconds at {1}x{2} to:`n{3}" -f $DurationSec, $size.Width, $size.Height, $finalOutput)
Write-Host "Start playing in 5 seconds..."
Start-Sleep -Seconds 5

& $ffmpeg `
    -y `
    -f gdigrab `
    -framerate 60 `
    -offset_x 0 `
    -offset_y 0 `
    -video_size ("{0}x{1}" -f $size.Width, $size.Height) `
    -i desktop `
    -t $DurationSec `
    -c:v libx264 `
    -preset veryfast `
    -crf 18 `
    -pix_fmt yuv420p `
    -movflags +faststart `
    $finalOutput

if ($LASTEXITCODE -ne 0) {
    throw "ffmpeg recording failed with exit code $LASTEXITCODE"
}

Write-Host "Recording complete:"
Write-Host $finalOutput
