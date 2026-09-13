# package.ps1 - Create a clean zip of StudyMate_Agent for submission.
# Run from INSIDE the StudyMate_Agent folder:
#   powershell -ExecutionPolicy Bypass -File package.ps1
#
# Output: ..\StudyMate_Agent.zip (one level up, outside this folder)

$ErrorActionPreference = "Stop"

$SrcDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ZipName = "StudyMate_Agent.zip"
$ZipDest = Join-Path (Split-Path $SrcDir -Parent) $ZipName

# Remove stale zip if it exists
if (Test-Path $ZipDest) { Remove-Item $ZipDest -Force }

# Clean __pycache__ and *.pyc before packing
Get-ChildItem -Path $SrcDir -Recurse -Directory -Filter "__pycache__" |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $SrcDir -Recurse -File -Filter "*.pyc" |
    Remove-Item -Force -ErrorAction SilentlyContinue

# Reset memory.json to clean state
$MemFile = Join-Path $SrcDir "memory.json"
@'
{
  "runs": 0,
  "weak_topics": [],
  "history": []
}
'@ | Set-Content -Path $MemFile -Encoding UTF8

# Build the zip
Compress-Archive -Path "$SrcDir\*" -DestinationPath $ZipDest -Force

Write-Host ""
Write-Host "============================================="
Write-Host "  Package created: $ZipDest"
Write-Host "  Size: $([math]::Round((Get-Item $ZipDest).Length / 1KB, 1)) KB"
Write-Host "============================================="
Write-Host ""
Write-Host "memory.json has been reset to clean runs:0."
Write-Host "__pycache__ and .pyc files removed."
Write-Host ""
Write-Host "Upload this zip or push the folder contents to GitHub."
