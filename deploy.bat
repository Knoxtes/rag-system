@echo off
REM RAG System Deployment Script for Windows/Plesk
REM This script sets up and starts the RAG system in a production environment

echo 🚀 Starting RAG System Deployment...
echo ==================================

REM Check for uncommitted changes
if exist .git (
    echo 🔍 Checking for uncommitted changes...
    
    REM Check if HEAD exists (repository has commits)
    git rev-parse --verify HEAD >nul 2>&1
    if %errorlevel% neq 0 (
        echo ℹ️  New repository with no commits yet
        echo.
    ) else (
        REM Check if there are any uncommitted changes
        git diff-index --quiet HEAD -- >nul 2>&1
        if %errorlevel% neq 0 (
            echo.
            echo ⚠️  WARNING: Uncommitted changes detected!
            echo.
            echo The following changes are uncommitted:
            git status --short
            echo.
            set "PROCEED="
            set /p "PROCEED=Do you want to proceed with deployment anyway? (y/N): "
            REM /i flag makes comparison case-insensitive (accepts y, Y, yes, Yes, YES)
            REM Empty input (just pressing Enter) will not match and falls through to cancel
            if /i "%PROCEED%"=="y" goto proceed
            if /i "%PROCEED%"=="yes" goto proceed
            echo ❌ Deployment cancelled. Please commit your changes first.
            exit /b 1
            :proceed
            echo ⚠️  Proceeding with uncommitted changes...
            echo.
        ) else (
            echo ✅ No uncommitted changes detected
            echo.
        )
    )
)

REM Check if Node.js is available
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 14+ first.
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python is not installed. Please install Python 3.8+ first.
        exit /b 1
    )
)

REM Install Node.js dependencies
echo 📦 Installing Node.js dependencies...
npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install Node.js dependencies.
    exit /b 1
)

REM Install Python dependencies
echo 🐍 Installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    python3 -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install Python dependencies.
        exit /b 1
    )
)

REM Build React frontend
echo ⚡ Building React frontend...
npm run build
if %errorlevel% neq 0 (
    echo ❌ React build failed. Please check for errors.
    exit /b 1
)

REM Check if build was successful
if not exist "chat-app\build\" (
    echo ❌ React build failed. Build directory not found.
    exit /b 1
)

REM Set environment variables for production
set NODE_ENV=production
set FLASK_ENV=production

echo ✅ Deployment complete!
echo.
echo 🌐 To start the server, run:
echo    npm start
echo.
echo 🔧 Environment:
node --version | findstr /R "v[0-9]"
python --version 2>nul || python3 --version
echo    Frontend build: ✅ Ready
echo    Backend ready: ✅ Ready

pause