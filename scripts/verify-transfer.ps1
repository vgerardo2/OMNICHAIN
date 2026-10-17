<#
Read-only transfer-integrity check. Validates manifest-relative paths, SHA-256
digests and lengths; rejects missing/changed/unexpected preparation files.
The unsigned manifest is excluded from its own hash set. This detects transfer
damage, not an attacker replacing both files and manifest. No file is executed
from the manifest and no source material is modified.
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
function Get-Sha256Hex {
    <# Hash exact file bytes using the .NET runtime so verification does not
    depend on optional PowerShell module discovery on a freshly installed PC.
    Streams and hash instances are disposed even on a failed read.
    #>
    param([string]$Path)
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '') }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}
$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$manifestPath = Join-Path $projectRoot 'TRANSFER-MANIFEST.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'TRANSFER-MANIFEST.json missing.' }
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.format_version -ne 1 -or @($manifest.files).Count -lt 1) { throw 'Unsupported or empty manifest.' }
$seen = @{}
$problems = @()
foreach ($entry in $manifest.files) {
    $relativePath = [string]$entry.path
    if ([string]::IsNullOrWhiteSpace($relativePath) -or [IO.Path]::IsPathRooted($relativePath) -or $relativePath.Contains(':') -or $relativePath -match '(^|[\\/])\.\.([\\/]|$)') { throw 'Manifest contains an invalid relative path.' }
    $normalizedPath = $relativePath.Replace('/', '\')
    if ($seen.ContainsKey($normalizedPath) -or $normalizedPath -eq 'TRANSFER-MANIFEST.json') { throw 'Manifest repeats a path or incorrectly includes itself.' }
    if ([string]$entry.sha256 -notmatch '^[0-9A-Fa-f]{64}$') { throw 'Malformed manifest SHA-256 value.' }
    $seen[$normalizedPath] = $true
    $absolutePath = [IO.Path]::GetFullPath((Join-Path $projectRoot $normalizedPath))
    if (-not $absolutePath.StartsWith($projectRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest path resolves outside the project.' }
    if (-not (Test-Path -LiteralPath $absolutePath -PathType Leaf)) { $problems += "Missing: $relativePath"; continue }
    $fileItem = Get-Item -LiteralPath $absolutePath -Force
    if ($fileItem.Length -ne [long]$entry.bytes) { $problems += "Length mismatch: $relativePath" }
    if ((Get-Sha256Hex -Path $absolutePath) -ne $entry.sha256) { $problems += "Digest mismatch: $relativePath" }
}
$ignoredTreePattern = '(^|\\)(\.venv|venv|node_modules|\.git|__pycache__|\.pytest_cache|runtime|reports)(\\|$)'
foreach ($file in Get-ChildItem -LiteralPath $projectRoot -Recurse -File -Force) {
    $relative = $file.FullName.Substring($projectRoot.Length + 1)
    if ($relative -eq 'TRANSFER-MANIFEST.json' -or $relative -match $ignoredTreePattern) { continue }
    if (-not $seen.ContainsKey($relative)) { $problems += "Unexpected preparation file: $relative" }
}
if ($problems.Count -gt 0) {
    [pscustomobject]@{Status='FAIL';Problems=$problems;Note='After intentional edits, use a newly reviewed manifest for a later snapshot; do not pretend the initial snapshot is unchanged.'} | ConvertTo-Json -Depth 4
    exit 1
}
[pscustomobject]@{Status='PASS';VerifiedFiles=$seen.Count;Scope='Initial preparation snapshot only';ManifestTrust='Unsigned; no independent authenticity claim';ApplicationTests='Not run'} | ConvertTo-Json
