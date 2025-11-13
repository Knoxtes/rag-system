@echo off
REM Deployment script for Windows/Plesk

echo 🚀 Starting RAG Chat System Deployment...

REM Check if Node.js is available
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js is not installed. Please install Node.js first.
    exit /b 1
)

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is not installed. Please install Python first.
    exit /b 1
)

echo 📦 Installing backend dependencies...
python -m pip install --user -r requirements-production.txt

echo 📦 Installing frontend dependencies...
npm install

echo 📦 Installing frontend app dependencies...
cd chat-app && npm install && cd ..

echo 🏗️  Building React frontend for production...
cd chat-app && npm run build && cd ..

echo ✅ Deployment complete!
echo.
echo 📝 Next steps for Plesk:
echo 1. Upload all files to your domain directory
echo 2. Set Python app entry point to: passenger_wsgi.py
echo 3. Set static files to serve from: chat-app/build/
echo 4. Configure environment variables in Plesk
echo 5. Restart the application
echo.
echo 🌐 The app will be available at your domain

pause