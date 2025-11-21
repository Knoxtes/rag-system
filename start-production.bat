@echo off
REM Production Startup Script for RAG System (Windows)
REM This script performs pre-flight checks and starts the application

echo ======================================
echo RAG System - Production Startup
echo ======================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found
    echo   Please create .env file with required variables
    exit /b 1
)

REM Check if credentials.json exists
if not exist "credentials.json" (
    echo [ERROR] credentials.json not found
    echo   Please add Google Cloud credentials
    exit /b 1
)

REM Check if React build exists
if not exist "chat-app\build" (
    echo [WARNING] React build not found
    echo   Running npm run build...
    call npm run build
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo [WARNING] Node modules not found
    echo   Running npm install...
    call npm install
)

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo [OK] Configuration loaded
echo.

echo ======================================
echo Starting RAG System...
echo ======================================
echo.

REM Start the application
npm start
