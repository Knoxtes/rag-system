@echo off
REM RAG System Startup Script with Flexible Port Configuration
REM This script allows you to run the system on any ports you prefer

echo 🚀 RAG System - Flexible Port Configuration
echo ================================================

REM Default ports (can be overridden by environment variables)
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=3000
if "%BACKEND_PORT%"=="" set BACKEND_PORT=5001
if "%NODE_ENV%"=="" set NODE_ENV=production

echo 🔧 Configuration:
echo    Frontend Port: %FRONTEND_PORT%
echo    Backend Port:  %BACKEND_PORT%
echo    Environment:   %NODE_ENV%
echo.

REM Set environment variables for the session
set PORT=%FRONTEND_PORT%
set FLASK_PORT=%BACKEND_PORT%
set REACT_APP_API_URL=http://localhost:%FRONTEND_PORT%

echo 📦 Installing dependencies...
call npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install Node.js dependencies
    pause
    exit /b 1
)

echo ⚡ Building React frontend...
call npm run build
if %errorlevel% neq 0 (
    echo ❌ Failed to build React frontend
    pause
    exit /b 1
)

echo ✅ Starting RAG System...
echo.
echo 🌐 Access your RAG system at: http://localhost:%FRONTEND_PORT%
echo 📊 Health check: http://localhost:%FRONTEND_PORT%/api/health
echo.
echo Press Ctrl+C to stop the server
echo.

call npm start