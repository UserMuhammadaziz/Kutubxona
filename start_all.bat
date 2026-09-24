@echo off
chcp 65001 >nul
title Kutubxona - Avtomatik ishga tushirish
echo ============================================
echo   Kutubxona loyihasini ishga tushirish
echo   (Redis + Celery worker + beat + Bot + Django)
echo ============================================
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0start_all.ps1"
echo.
pause