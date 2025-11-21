#!/bin/bash

# RAG System Deployment Script for Plesk
# Optimized for Ask.7MountainsMedia.com
# Target: Plesk Obsidian 18.0.73 on AlmaLinux 9.7 with Node.js 25.2.0

echo "🚀 RAG System Deployment for Ask.7MountainsMedia.com"
echo "======================================================"
echo ""

# Detect if running on Plesk
PLESK_NODE_PATH="/opt/plesk/node/25/bin"
if [ -d "$PLESK_NODE_PATH" ]; then
    echo "✅ Detected Plesk environment"
    NODE_CMD="$PLESK_NODE_PATH/node"
    NPM_CMD="$PLESK_NODE_PATH/npm"
    export PATH="$PLESK_NODE_PATH:$PATH"
else
    echo "ℹ️  Using system Node.js"
    NODE_CMD="node"
    NPM_CMD="npm"
fi

# Check Node.js version
NODE_VERSION=$($NODE_CMD --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
if [ -z "$NODE_VERSION" ]; then
    echo "❌ Node.js is not installed. Please install Node.js 25.2.0 first."
    exit 1
fi

if [ "$NODE_VERSION" -lt 25 ]; then
    echo "⚠️  Warning: Node.js $NODE_VERSION detected. Recommended: 25.2.0+"
    echo "   The application may work but is optimized for Node.js 25.2.0"
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION detected"

# Install Node.js dependencies
echo ""
echo "📦 Installing Node.js dependencies..."
$NPM_CMD install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

# Install Python dependencies
echo ""
echo "🐍 Installing Python dependencies..."
if [ -f "requirements-production.txt" ]; then
    python3 -m pip install --user -r requirements-production.txt
    if [ $? -ne 0 ]; then
        echo "⚠️  Warning: Some Python dependencies may have failed to install"
        echo "   Continuing with deployment..."
    fi
else
    echo "⚠️  Warning: requirements-production.txt not found, using requirements.txt"
    python3 -m pip install --user -r requirements.txt
fi

# Build React frontend
echo ""
echo "⚡ Building React frontend..."
$NPM_CMD run build
if [ $? -ne 0 ]; then
    echo "❌ React build failed. Please check for errors above."
    exit 1
fi

# Check if build was successful
if [ ! -d "chat-app/build" ]; then
    echo "❌ Build directory not found. Build may have failed."
    exit 1
fi

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    echo ""
    echo "📁 Creating logs directory..."
    mkdir -p logs
    chmod 755 logs
fi

# Set environment variables for production
export NODE_ENV=production
export FLASK_ENV=production

echo ""
echo "✅ Deployment complete!"
echo "======================================================"
echo ""
echo "🌐 Domain: Ask.7MountainsMedia.com"
echo "🔧 Environment:"
echo "   - Node.js version: $($NODE_CMD --version)"
echo "   - Python version: $(python3 --version)"
echo "   - Frontend build: ✅ chat-app/build/"
echo "   - Backend ready: ✅ Python dependencies installed"
echo ""
echo "📋 Next Steps:"
echo ""
echo "   1. Upload required files (if not already present):"
echo "      - credentials.json"
echo "      - token.pickle"
echo "      - .env (with production settings)"
echo ""
echo "   2. Configure environment variables in Plesk"
echo ""
echo "   3. Start the server:"
echo "      npm start"
echo ""
echo "   4. Or restart in Plesk:"
echo "      Domains → Ask.7MountainsMedia.com → Node.js → Restart"
echo ""
echo "📖 For detailed setup instructions, see PLESK_SETUP_GUIDE.md"
echo ""