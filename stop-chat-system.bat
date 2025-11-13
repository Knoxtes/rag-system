@echo off
title Stop RAG Chat System
echo ====================================================================
echo                     STOPPING RAG CHAT SYSTEM
echo ====================================================================
echo.
echo Stopping all chat system processes...
echo.

echo Stopping Node.js processes (React app)...
taskkill /f /im node.exe 2>nul
if %errorlevel%==0 (
    echo   ✓ React app stopped
) else (
    echo   - No React app processes found
)

echo Stopping Python processes (Flask API)...
for /f "tokens=2 delims=," %%a in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "chat_api"') do (
    taskkill /f /pid %%a 2>nul
)
echo   ✓ Flask API stopped

echo.
echo ====================================================================
echo                    ALL SERVICES STOPPED
echo ====================================================================
echo.
echo All RAG Chat System services have been stopped.
echo.
echo Press any key to close...
pause >nul