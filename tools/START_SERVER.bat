@echo off
chcp 65001 >nul
title Xiaozhi server - start
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0xiaozhi.ps1" start
pause
