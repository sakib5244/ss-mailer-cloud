@echo off
setlocal
cd /d "%~dp0"
echo Installing required packages...
py -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto fail
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
py -m PyInstaller --noconfirm --clean --windowed --onefile --name SS_Mailer_User --icon ss_mailer.ico --add-data "ss_mailer.ico;." --add-data "cloud_config.ini;." cloud_user_app.py
if errorlevel 1 goto fail
py -m PyInstaller --noconfirm --clean --windowed --onefile --name SS_Mailer_Admin --icon ss_mailer.ico --add-data "ss_mailer.ico;." --add-data "cloud_config.ini;." cloud_admin_app.py
if errorlevel 1 goto fail
py -m PyInstaller --noconfirm --clean --windowed --onefile --name SS_Mailer_Subadmin --icon ss_mailer.ico --add-data "ss_mailer.ico;." --add-data "cloud_config.ini;." cloud_subadmin_app.py
if errorlevel 1 goto fail
copy /Y cloud_config.ini dist\cloud_config.ini >nul
copy /Y ss_mailer.ico dist\ss_mailer.ico >nul
echo BUILD COMPLETE: dist\SS_Mailer_User.exe, dist\SS_Mailer_Admin.exe, dist\SS_Mailer_Subadmin.exe
echo Configure dist\cloud_config.ini with your deployed HTTPS server URL.
pause
exit /b 0
:fail
echo Build failed.
pause
exit /b 1
