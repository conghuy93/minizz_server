@echo off
chcp 65001 >nul
title Xiaozhi server - status
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0xiaozhi.ps1" status
pause
