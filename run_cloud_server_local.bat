@echo off
setlocal
cd /d "%~dp0"
if "%SSMAILER_ADMIN_PASSWORD%"=="" (
  echo Set SSMAILER_ADMIN_PASSWORD to a strong admin password first.
  set /p SSMAILER_ADMIN_PASSWORD=Enter strong Admin password: 
)
if "%SSMAILER_TOKEN_SECRET%"=="" set SSMAILER_TOKEN_SECRET=%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%
set FLASK_APP=cloud_server.py
py -m pip install -r requirements.txt
py cloud_server.py
pause
