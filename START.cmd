@echo off
powershell.exe -NoProfile -File "%~dp0scripts\Start-Checkmate.ps1" %*
set "CHECKMATE_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %CHECKMATE_EXIT%
