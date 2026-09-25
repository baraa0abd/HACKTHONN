$ErrorActionPreference = 'Stop'
$pythonExe = 'C:\Users\liqaa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { $pythonExe = 'python' }
Push-Location $PSScriptRoot
try {
    & $pythonExe verify.py
    if ($LASTEXITCODE -ne 0) { throw 'Dashboard verification failed' }
    & $pythonExe serve.py
} finally { Pop-Location }
