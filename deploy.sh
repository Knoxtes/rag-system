#!/bin/bash

# RAG System Deployment Script for Plesk
# This script sets up and starts the RAG system in a production environment

echo "🚀 Starting RAG System Deployment..."
echo "=================================="

# Check for uncommitted changes
if command -v git &> /dev/null; then
    if [ -d .git ]; then
        if ! git diff-index --quiet HEAD -- 2>/dev/null; then
            echo "⚠️  Uncommitted changes detected"
            echo ""
            echo "You have uncommitted changes in your repository."
            echo "It's recommended to commit or stash your changes before deploying."
            echo ""
            read -p "Do you want to proceed anyway? (y/N): " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "❌ Deployment cancelled."
                exit 1
            fi
            echo "✅ Proceeding with deployment..."
            echo ""
        fi
    fi
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 14+ first."
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if command -v python &> /dev/null; then
    python -m pip install -r requirements.txt
else
    python3 -m pip install -r requirements.txt
fi

# Build React frontend
echo "⚡ Building React frontend..."
npm run build

# Check if build was successful
if [ ! -d "chat-app/build" ]; then
    echo "❌ React build failed. Please check for errors."
    exit 1
fi

# Set environment variables for production
export NODE_ENV=production
export FLASK_ENV=production

echo "✅ Deployment complete!"
echo ""
echo "🌐 To start the server, run:"
echo "   npm start"
echo ""
echo "🔧 Environment:"
echo "   - Node.js version: $(node --version)"
echo "   - Python version: $(python --version 2>/dev/null || python3 --version)"
echo "   - Frontend build: ✅ Ready"
echo "   - Backend ready: ✅ Ready"