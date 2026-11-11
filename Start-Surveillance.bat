@echo off
setlocal
set "ROOT=%~dp0"

curl.exe -fsS http://localhost:8080/api/health | findstr /C:"AI Smart Surveillance API" >nul
if errorlevel 1 (
    echo Starting Spring Boot backend...
    start "Surveillance Backend" /D "%ROOT%spring-backend" cmd /k mvn spring-boot:run
) else (
    echo Backend is already running.
)

set /a attempts=0
:wait_for_backend
curl.exe -fsS http://localhost:8080/api/health | findstr /C:"AI Smart Surveillance API" >nul
if not errorlevel 1 goto backend_ready
set /a attempts+=1
if %attempts% GEQ 90 (
    echo Backend did not become ready. Check the Surveillance Backend window for errors.
    pause
    exit /b 1
)
timeout /t 2 /nobreak >nul
goto wait_for_backend

:backend_ready
echo Starting webcam detector...
start "Surveillance Detector" /D "%ROOT%python-ai" cmd /k ""%ROOT%python-ai\.venv\Scripts\python.exe" detector.py --source 0 --fire-model "..\models\fire_smoke.pt" --weapon-model "..\models\weapons.pt""
start "" http://localhost:8080
