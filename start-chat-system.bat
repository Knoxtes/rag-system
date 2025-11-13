@echo off
title RAG Chat System Startup
echo ====================================================================
echo                    RAG CHAT SYSTEM - COMPLETE STARTUP
echo ====================================================================
echo.
echo Starting both Flask API and React Chat App...
echo.

echo [1/2] Starting Flask API Server on port 5000...
start "Flask API" powershell -Command "cd 'c:\Users\Notxe\Desktop\rag-system'; Write-Host 'Starting Flask API Server...' -ForegroundColor Green; python chat_api.py"

echo [2/2] Starting React Chat App on port 3001...
timeout /t 3 /nobreak >nul
start "React Chat App" powershell -Command "cd 'c:\Users\Notxe\Desktop\rag-system\chat-app'; Write-Host 'Starting React Chat App...' -ForegroundColor Cyan; `$env:PORT=3001; npm start"

echo.
echo ====================================================================
echo                           STARTUP COMPLETE
echo ====================================================================
echo.
echo Your RAG Chat System is now starting up!
echo.
echo Services:
echo   - Flask API:     http://localhost:5000
echo   - React Chat:    http://localhost:3001
echo.
echo The React app should open automatically in your browser.
echo If not, navigate to: http://localhost:3001
echo.
echo Press any key to close this window...
pause >nul