<#
Prepare only this project's Python virtual environment using the selected
installed interpreter. No package downloads, activation-policy edits, global
installs, Git operations or model calls occur. Existing environments are
checked rather than overwritten. -CheckOnly performs no mutation.
#>
[CmdletBinding()]
param([string]$PythonExecutable='python', [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'

$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$environmentPath = [IO.Path]::GetFullPath((Join-Path $projectRoot '.venv'))
if (-not $environmentPath.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Environment destination is outside the project.'
}
$pythonCommand = Get-Command $PythonExecutable -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $pythonCommand) { throw 'Python executable not found. Install a suitable Windows ARM64 Python or pass -PythonExecutable with its exact executable path.' }
$probeCode = 'import json,platform,sys,sqlite3,ssl,venv; print(json.dumps(dict(version=sys.version.split()[0],major=sys.version_info[0],minor=sys.version_info[1],machine=platform.machine(),bits=64 if sys.maxsize>2**32 else 32,sqlite=sqlite3.sqlite_version,prefix=sys.prefix,base_prefix=sys.base_prefix)))'
$baseJson = & $pythonCommand.Source -c $probeCode
if ($LASTEXITCODE -ne 0) { throw 'Installed Python could not load required standard-library modules.' }
$baseInfo = $baseJson | ConvertFrom-Json
if ($baseInfo.major -ne 3 -or $baseInfo.minor -lt 11 -or $baseInfo.bits -ne 64) { throw 'Use 64-bit Python 3.11 or newer; proposed project target is native ARM64 Python 3.14.' }
if ($baseInfo.machine -notmatch '^(ARM64|aarch64)$') {
    Write-Warning "Selected interpreter reports $($baseInfo.machine). This is not a verified native ARM64 laptop environment."
}
$venvPython = Join-Path $environmentPath 'Scripts\python.exe'
if (Test-Path -LiteralPath $environmentPath) {
    $environmentItem = Get-Item -LiteralPath $environmentPath -Force
    if (-not $environmentItem.PSIsContainer -or ($environmentItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Existing .venv is not an ordinary project directory; refusing mutation.' }
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) { throw 'Existing .venv has no Windows Python executable; inspect it manually. Nothing was overwritten.' }
}
if ($CheckOnly) {
    [pscustomobject]@{Mode='CHECK_ONLY';ProjectRoot=$projectRoot;SelectedPython=$pythonCommand.Source;Base=$baseInfo;EnvironmentExists=(Test-Path -LiteralPath $environmentPath);Destination=$environmentPath;Downloads='None';Changes='None'} | ConvertTo-Json -Depth 5
    exit 0
}
$createdEnvironment = $false
if (-not (Test-Path -LiteralPath $environmentPath)) {
    & $pythonCommand.Source -m venv $environmentPath
    if ($LASTEXITCODE -ne 0) { throw 'Environment creation failed. Inspect any partial .venv; no automatic cleanup or overwrite was attempted.' }
    $createdEnvironment = $true
}
$environmentJson = & $venvPython -c $probeCode
if ($LASTEXITCODE -ne 0) { throw 'Project Python import check failed; no environment upgrade was attempted.' }
$environmentInfo = $environmentJson | ConvertFrom-Json
$resolvedPrefix = [IO.Path]::GetFullPath([string]$environmentInfo.prefix).TrimEnd('\')
if (-not $resolvedPrefix.Equals($environmentPath.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase) -or $environmentInfo.prefix -eq $environmentInfo.base_prefix) {
    throw 'Interpreter does not identify this project virtual environment; refuse to treat it as ready.'
}
$pipOutput = & $venvPython -m pip --version
if ($LASTEXITCODE -ne 0) { throw 'Project pip check failed; no network installation was attempted.' }
[pscustomobject]@{Mode='ENVIRONMENT_CHECK';Created=$createdEnvironment;Python=$environmentInfo;Pip=$pipOutput;Downloads='None';ApplicationTests='Not run; application not implemented';Next='Record actual laptop architecture and environment status in CHECKPOINT.md.'} | ConvertTo-Json -Depth 5
