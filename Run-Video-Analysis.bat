@echo off
set "ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%ROOT%Run-Video-Analysis.ps1"
