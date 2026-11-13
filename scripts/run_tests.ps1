$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "reports/test_evidence") | Out-Null
Push-Location (Join-Path $ProjectRoot "backend")
try {
    .\.venv\Scripts\python.exe -m pytest tests -q --basetemp .pytest-tmp --junitxml ..\reports\test_evidence\pytest-results.xml
} finally {
    Pop-Location
}
