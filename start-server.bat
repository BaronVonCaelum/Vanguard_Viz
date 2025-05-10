@echo off
echo Starting Node.js server...

REM Change to the project directory
cd /d "D:\Vanguard Viz"
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to change directory to D:\Vanguard Viz
    pause
    exit /b %ERRORLEVEL%
)

REM Check if Node.js is installed
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Node.js is not installed or not in the PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if server.js exists
if not exist server.js (
    echo Error: server.js file not found in D:\Vanguard Viz
    pause
    exit /b 1
)

echo Starting the server...
echo Press Ctrl+C to stop the server
node server.js
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to start the Node.js server
    pause
    exit /b %ERRORLEVEL%
)

pause

