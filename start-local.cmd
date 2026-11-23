@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment missing: .venv\Scripts\python.exe
  echo See PERSONAL_DEPLOY.md for setup instructions.
  pause
  exit /b 1
)
if not exist "frontend\dist\index.html" (
  echo Frontend build missing. See PERSONAL_DEPLOY.md to build and install it.
  pause
  exit /b 1
)
set "ZFUNDPILOT_HOME=%~dp0"
set "ZFUNDPILOT_TIMEZONE=Asia/Shanghai"
echo ZFundPilot: http://127.0.0.1:8000
echo Close this window or press Ctrl+C to stop the server.
".venv\Scripts\python.exe" -m uvicorn zfundpilot.api:app --host 127.0.0.1 --port 8000
if errorlevel 1 pause
