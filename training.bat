@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto run

echo Python environment not found: .venv
echo Run setup.bat first.
pause
exit /b 1

:run
rem Мастер запускается из корня проекта: production-функции читают
rem project/configuration/*.json по относительным путям.
".venv\Scripts\python.exe" -m project.training --open-browser %*
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause
endlocal & exit /b %EXIT_CODE%
