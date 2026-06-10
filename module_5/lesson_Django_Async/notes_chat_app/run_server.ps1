# run_server.ps1 — запуск ASGI сервера для notes_chat_app
# Використання: правий клік → Run with PowerShell
#           або: cd до папки, потім .\run_server.ps1

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

$env:PYTHONPATH = $ProjectDir
$env:DJANGO_SETTINGS_MODULE = "notes_project.settings"

Write-Host "Project: $ProjectDir" -ForegroundColor Green
Write-Host "Starting uvicorn on http://127.0.0.1:8001 ..." -ForegroundColor Cyan

python -m uvicorn notes_project.asgi:application --reload --port 8001
