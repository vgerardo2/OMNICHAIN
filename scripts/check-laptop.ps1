<#
Read-only OmniChain preparation diagnostic for Windows PowerShell 5.1+.
Reports only selected tool versions, architecture, disk space and permitted
hardware metadata. It makes no model/network requests, installs nothing and
does not print secrets or enumerate the full environment. Output may contain
local executable paths; review it before sharing or publishing.
#>
[CmdletBinding()]
param([switch]$SkipHardware)
$ErrorActionPreference = 'Stop'

function Get-ToolObservation {
    <# Resolve one allowlisted command and optionally obtain a bounded version
    response. Ollama/editor/installers are presence-only to avoid opening an
    app, contacting a server or prompting for installation during diagnostics.
    #>
    param([string]$Name, [string[]]$VersionArguments, [bool]$ProbeVersion)
    $toolCommand = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $toolCommand) {
        return [pscustomobject]@{Tool=$Name;Found=$false;Path=$null;Version=$null;Error=$null}
    }
    $versionText = $null
    $versionError = $null
    if ($ProbeVersion) {
        try {
            $versionLines = @(& $toolCommand.Source @VersionArguments 2>&1)
            $versionExit = $LASTEXITCODE
            $versionText = ($versionLines | Select-Object -First 5 | Out-String).Trim()
            if ($versionExit -ne 0) { $versionError = "Version probe exited $versionExit" }
        } catch { $versionError = $_.Exception.Message }
    }
    return [pscustomobject]@{Tool=$Name;Found=$true;Path=$toolCommand.Source;Version=$versionText;Error=$versionError}
}

$toolDefinitions = @(
    @{Name='python';Arguments=@('--version');Probe=$true},
    @{Name='py';Arguments=@('--version');Probe=$true},
    @{Name='git';Arguments=@('--version');Probe=$true},
    @{Name='node';Arguments=@('--version');Probe=$true},
    @{Name='npm.cmd';Arguments=@('--version');Probe=$true},
    @{Name='code.cmd';Arguments=@();Probe=$false},
    @{Name='ollama';Arguments=@();Probe=$false}
)
$toolResults = @(foreach ($definition in $toolDefinitions) {
    Get-ToolObservation -Name $definition.Name -VersionArguments $definition.Arguments -ProbeVersion $definition.Probe
})
$pythonDetails = $null
$pythonError = $null
$pythonCommand = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pythonCommand) {
    try {
        $pythonJson = & $pythonCommand.Source -c 'import json,platform,sys,sqlite3,ssl,venv; print(json.dumps(dict(version=sys.version.split()[0],machine=platform.machine(),bits=64 if sys.maxsize>2**32 else 32,sqlite=sqlite3.sqlite_version,stdlib_checks=True)))'
        if ($LASTEXITCODE -ne 0) { throw 'Python import probe failed.' }
        $pythonDetails = $pythonJson | ConvertFrom-Json
    } catch { $pythonError = $_.Exception.Message }
}
$hardware = $null
$hardwareError = $null
if (-not $SkipHardware) {
    try {
        $machineInfo = Get-CimInstance Win32_ComputerSystem -ErrorAction Stop
        $cpuInfo = Get-CimInstance Win32_Processor -ErrorAction Stop | Select-Object -First 1
        $videoInfo = @(Get-CimInstance Win32_VideoController -ErrorAction Stop | Select-Object -ExpandProperty Name)
        $hardware = [pscustomobject]@{CPU=$cpuInfo.Name;RAMGiB=[math]::Round($machineInfo.TotalPhysicalMemory/1GB,1);Graphics=$videoInfo}
    } catch { $hardwareError = 'Hardware query unavailable in this session; no elevation attempted.' }
}
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectDriveName = (Get-Item -LiteralPath $projectRoot).PSDrive.Name
$projectDrive = Get-PSDrive -Name $projectDriveName
[pscustomobject]@{
    Diagnostic='OmniChain laptop preparation; no application test or model call'
    PowerShellVersion=$PSVersionTable.PSVersion.ToString()
    ProcessArchitecture=$env:PROCESSOR_ARCHITECTURE
    NativeArchitectureHint=$env:PROCESSOR_ARCHITEW6432
    OSVersion=[Environment]::OSVersion.Version.ToString()
    Is64BitOS=[Environment]::Is64BitOperatingSystem
    FreeProjectDriveGiB=if ($null -ne $projectDrive.Free) {[math]::Round($projectDrive.Free/1GB,1)} else {$null}
    Tools=$toolResults
    Python=$pythonDetails
    PythonError=$pythonError
    Hardware=$hardware
    HardwareError=$hardwareError
    Next='Record laptop observations in CHECKPOINT.md; do not infer app or model readiness.'
} | ConvertTo-Json -Depth 6
