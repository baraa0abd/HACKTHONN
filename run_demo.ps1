$ErrorActionPreference = 'Stop'
$pythonExe = 'C:\Users\liqaa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { $pythonExe = 'python' }
Push-Location $PSScriptRoot
try {
    & $pythonExe real_challenge1.py
    if ($LASTEXITCODE -ne 0) { throw 'Demo failed' }
} finally { Pop-Location }
