#!/usr/bin/env bash
# Deployment script for Plesk

echo "🚀 Starting RAG Chat System Deployment..."

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python first."
    exit 1
fi

# Set Python command
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "📦 Installing backend dependencies..."
$PYTHON_CMD -m pip install --user -r requirements-production.txt

echo "📦 Installing frontend dependencies..."
npm install

echo "📦 Installing frontend app dependencies..."
cd chat-app && npm install && cd ..

echo "🏗️  Building React frontend for production..."
cd chat-app && npm run build && cd ..

echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps for Plesk:"
echo "1. Upload all files to your domain directory"
echo "2. Set Python app entry point to: passenger_wsgi.py" 
echo "3. Set static files to serve from: chat-app/build/"
echo "4. Configure environment variables in Plesk"
echo "5. Restart the application"
echo ""
echo "🌐 The app will be available at your domain"