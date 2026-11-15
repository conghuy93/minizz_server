@echo off
chcp 65001 >nul
title Xiaozhi server - stop
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0xiaozhi.ps1" stop
pause
