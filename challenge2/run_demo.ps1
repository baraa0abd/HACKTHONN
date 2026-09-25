$ErrorActionPreference = 'Stop'
$pythonExe = 'C:\Users\liqaa\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { $pythonExe = 'python' }
Push-Location $PSScriptRoot
try {
    & $pythonExe run_real.py
    if ($LASTEXITCODE -ne 0) { throw 'OrbitBench build or verification failed' }
} finally { Pop-Location }
