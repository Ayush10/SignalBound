Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class KeySender {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, int dwFlags, int dwExtraInfo);
    public const byte VK_CONTROL = 0x11;
    public const byte VK_MENU = 0x12;
    public const byte VK_F11 = 0x7A;
    public const int KEYEVENTF_KEYUP = 0x0002;
}
"@
Add-Type -AssemblyName System.Windows.Forms
$wshell = New-Object -ComObject WScript.Shell

$procs = Get-Process UnrealEditor -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 }
if (-not $procs) {
    $procs = Get-Process |
        Where-Object { $_.MainWindowTitle -like '*Unreal Editor*' -or $_.MainWindowTitle -like '*SignalBound*' }
}
foreach ($p in $procs) {
    Write-Host "Found: $($p.MainWindowTitle) (PID: $($p.Id))"
    $activated = $wshell.AppActivate($p.Id)
    if (-not $activated) {
        [KeySender]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    }
    Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait("^%{F11}")
    Write-Host "Sent Ctrl+Alt+F11 to trigger Live Coding (activated=$activated)"
    break
}

if (-not $procs) {
    Write-Host "No Unreal Editor window found"
}
