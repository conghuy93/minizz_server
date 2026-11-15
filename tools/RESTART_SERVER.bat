@echo off
chcp 65001 >nul
title Xiaozhi server - restart
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0xiaozhi.ps1" restart
pause
