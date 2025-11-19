#!/bin/bash

# RAG System Startup Script with Flexible Port Configuration
# This script allows you to run the system on any ports you prefer

echo "🚀 RAG System - Flexible Port Configuration"
echo "================================================"

# Default ports (can be overridden by environment variables)
export FRONTEND_PORT=${FRONTEND_PORT:-3000}
export BACKEND_PORT=${BACKEND_PORT:-5001}
export NODE_ENV=${NODE_ENV:-production}

echo "🔧 Configuration:"
echo "   Frontend Port: $FRONTEND_PORT"
echo "   Backend Port:  $BACKEND_PORT"
echo "   Environment:   $NODE_ENV"
echo ""

# Set environment variables for the session
export PORT=$FRONTEND_PORT
export FLASK_PORT=$BACKEND_PORT
export REACT_APP_API_URL=http://localhost:$FRONTEND_PORT

echo "📦 Installing dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi

echo "⚡ Building React frontend..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Failed to build React frontend"
    exit 1
fi

echo "✅ Starting RAG System..."
echo ""
echo "🌐 Access your RAG system at: http://localhost:$FRONTEND_PORT"
echo "📊 Health check: http://localhost:$FRONTEND_PORT/api/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start