$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $ProjectRoot "backend")
try {
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
