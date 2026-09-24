# =============================================================
#  Kutubxona - hammasini bitta buyruq bilan ishga tushirish
#  Foydalanish:  powershell -ExecutionPolicy Bypass -File .\start_all.ps1
#  Parametrlar:
#    -SkipBot     Telegram botni ishga tushirmaslik
#    -SkipDjango  Django serverni ishga tushirmaslik
# =============================================================

param(
    [switch]$SkipBot,
    [switch]$SkipDjango
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Logs = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

$CeleryExe = Join-Path $Root "venv\Scripts\celery.exe"
$PythonExe = Join-Path $Root "venv\Scripts\python.exe"

# -------------------------------------------------------------
# 1) Redis (Memurai xizmati) tayyormi?
# -------------------------------------------------------------
Write-Host "==> Redis (Memurai) tekshirilmoqda..." -ForegroundColor Cyan
$service = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Warning "Memurai xizmati topilmadi. Redis ishlamaydi!"
} elseif ($service.Status -ne "Running") {
    Write-Host "    Memurai xizmati ishga tushirilmoqda..."
    Start-Service -Name "Memurai"
}
if (Get-NetTCPConnection -LocalPort 6379 -State Listen -ErrorAction SilentlyContinue) {
    Write-Host "    Redis ishlamoqda (port 6379)." -ForegroundColor Green
} else {
    Write-Warning "Port 6379 bog'lanmadi. Memurai/Redis yoqilganligini tekshiring."
}

# -------------------------------------------------------------
# 2) Eski Celery jarayonlarini tozalash
# -------------------------------------------------------------
Write-Host "==> Eski Celery jarayonlari tozalanmoqda..." -ForegroundColor Cyan
Get-Process | Where-Object { $_.ProcessName -like "celery*" -or ($_.ProcessName -eq "python" -and $_.Path -like "*Kutubxona*") } |
    Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# -------------------------------------------------------------
# 3) Celery worker (jarima, navbat, eslatma vazifalari)
# -------------------------------------------------------------
Write-Host "==> Celery worker ishga tushirilmoqda..." -ForegroundColor Cyan
Start-Process -FilePath $CeleryExe `
    -ArgumentList "-A", "config", "worker", "-l", "info", "--pool=solo", "--pidfile=celery_worker.pid" `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $Logs "celery_worker.out.log") `
    -RedirectStandardError (Join-Path $Logs "celery_worker.err.log") | Out-Null

# -------------------------------------------------------------
# 4) Celery beat (jadval bo'yicha ishlash)
# -------------------------------------------------------------
Write-Host "==> Celery beat ishga tushirilmoqda..." -ForegroundColor Cyan
Start-Process -FilePath $CeleryExe `
    -ArgumentList "-A", "config", "beat", "-l", "info", "--pidfile=celery_beat.pid", "--schedule=celerybeat-schedule" `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $Logs "celery_beat.out.log") `
    -RedirectStandardError (Join-Path $Logs "celery_beat.err.log") | Out-Null

# -------------------------------------------------------------
# 5) Telegram bot
# -------------------------------------------------------------
if (-not $SkipBot) {
    Write-Host "==> Telegram bot ishga tushirilmoqda..." -ForegroundColor Cyan
    Start-Process -FilePath $PythonExe `
        -ArgumentList "bot\main.py" `
        -WorkingDirectory $Root `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $Logs "bot.out.log") `
        -RedirectStandardError (Join-Path $Logs "bot.err.log") | Out-Null
} else {
    Write-Host "==> Bot o'tkazib yuborildi (-SkipBot)." -ForegroundColor DarkGray
}

# -------------------------------------------------------------
# 6) Django server
# -------------------------------------------------------------
if (-not $SkipDjango) {
    Write-Host "==> Django server ishga tushirilmoqda..." -ForegroundColor Cyan
    Start-Process -FilePath $PythonExe `
        -ArgumentList "manage.py", "runserver" `
        -WorkingDirectory $Root `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $Logs "django.out.log") `
        -RedirectStandardError (Join-Path $Logs "django.err.log") | Out-Null
} else {
    Write-Host "==> Django o'tkazib yuborildi (-SkipDjango)." -ForegroundColor DarkGray
}

Start-Sleep -Seconds 3
Write-Host ""
Write-Host "Hammasi ishga tushdi!" -ForegroundColor Green
Write-Host "  Celery worker   -> logs\celery_worker.out.log"   -ForegroundColor Gray
Write-Host "  Celery beat     -> logs\celery_beat.out.log"     -ForegroundColor Gray
Write-Host "  Telegram bot    -> logs\bot.out.log"             -ForegroundColor Gray
Write-Host "  Django server   -> logs\django.out.log"          -ForegroundColor Gray
Write-Host "To'xtatish uchun: powershell -ExecutionPolicy Bypass -File .\stop_all.ps1" -ForegroundColor Yellow