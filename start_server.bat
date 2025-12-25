@echo off
REM OACA Server Startup Script for Windows
REM This script starts the Flask server and displays network access information

echo.
echo ============================================================
echo   OACA Aviation Administration - Server Startup
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Get the local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    set IP=!IP: =!
    echo Found IP address: !IP!
)

echo.
echo Starting server...
echo.

REM Start the Python server
python start_server.py

pause

