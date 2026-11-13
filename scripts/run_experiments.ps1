$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $ProjectRoot "backend")
try {
    .\.venv\Scripts\python.exe -m app.experiment_cli @args
} finally {
    Pop-Location
}
