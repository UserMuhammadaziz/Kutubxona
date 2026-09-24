# =============================================================
#  Kutubxona - Celery, bot va Django jarayonlarini to'xtatish
#  Foydalanish: powershell -ExecutionPolicy Bypass -File .\stop_all.ps1
# =============================================================

$ErrorActionPreference = "SilentlyContinue"

Write-Host "==> Jarayonlar to'xtatilmoqda..." -ForegroundColor Cyan

# Celery worker/beat ning o'z pidfayllaridan to'xtatish
Get-Process | Where-Object { $_.ProcessName -like "celery*" } | Stop-Process -Force

# Django va bot (project papkasidagi python jarayonlari)
Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -like "*Kutubxona*" } |
    Stop-Process -Force

Start-Sleep -Seconds 2

Write-Host "Barcha jarayonlar to'xtatildi. (Redis/Memurai xizmati ishlab qoladi)" -ForegroundColor Green