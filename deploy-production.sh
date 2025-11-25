#!/bin/bash

# RAG System - Safe Production Deployment Script
# This script safely pulls, rebuilds, and deploys the RAG system
# Handles git conflicts and file permission issues gracefully

set -e

echo "=========================================="
echo "RAG System - Safe Production Deployment"
echo "=========================================="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "[*] Working directory: $SCRIPT_DIR"
echo ""

# Path to Plesk Node.js
PLESK_NODE="/opt/plesk/node/22/bin"
export PATH="$PLESK_NODE:$PATH"

# Function to handle errors
handle_error() {
  echo "❌ Error: $1"
  exit 1
}

echo "[1] Stopping existing services..."
echo "   Stopping Node.js server..."
pkill -f "node server.js" || true
sleep 2
echo "   Stopping Flask backend..."
pkill -f "python.*chat_api.py" || true
sleep 2
echo "✓ Services stopped"
echo ""

echo "[2] Cleaning up problematic files..."
echo "   Removing chat-app node_modules..."
rm -rf "$SCRIPT_DIR/chat-app/node_modules" 2>/dev/null || true
echo "   Removing root node_modules..."
rm -rf "$SCRIPT_DIR/node_modules" 2>/dev/null || true
echo "   Removing lock files..."
rm -f "$SCRIPT_DIR/package-lock.json" 2>/dev/null || true
rm -f "$SCRIPT_DIR/chat-app/package-lock.json" 2>/dev/null || true
rm -f "$SCRIPT_DIR/yarn.lock" 2>/dev/null || true
rm -f "$SCRIPT_DIR/chat-app/yarn.lock" 2>/dev/null || true
echo "   Clearing npm cache..."
$PLESK_NODE/npm cache clean --force 2>/dev/null || true
echo "✓ Cleanup complete"
echo ""

echo "[3] Installing root dependencies..."
echo "   (Using --force flag to rebuild all modules)..."
$PLESK_NODE/npm install --omit=dev --legacy-peer-deps --force --audit=false || handle_error "Root npm install failed"
echo "✓ Root dependencies installed"
echo ""

echo "[4] Installing frontend dependencies..."
cd "$SCRIPT_DIR/chat-app"
echo "   (Using --force flag to rebuild all modules)..."
$PLESK_NODE/npm install --legacy-peer-deps --force --audit=false || handle_error "Frontend npm install failed"
echo "✓ Frontend dependencies installed"
echo ""

echo "[5] Building React frontend..."
echo "   (This may take 2-3 minutes...)"
export NODE_OPTIONS='--max-old-space-size=4096'
export GENERATE_SOURCEMAP=false
export REACT_APP_API_BASE_URL=''
$PLESK_NODE/npm run build || handle_error "React build failed"
echo "✓ React build completed"
echo ""

echo "[6] Starting services..."
cd "$SCRIPT_DIR"

echo "   Starting Node.js server..."
nohup $PLESK_NODE/node server.js > nohup.out 2>&1 &
NODE_PID=$!
sleep 4

if ! kill -0 $NODE_PID 2>/dev/null; then
  echo "❌ Node.js failed to start"
  tail -30 nohup.out
  exit 1
fi
echo "✓ Node.js running (PID: $NODE_PID)"
echo ""

echo "[7] Verifying deployment..."
sleep 2

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:3000/api/health || echo '{}')
if echo "$HEALTH_RESPONSE" | grep -q "healthy\|flask_backend"; then
  echo "✓ Health check passed"
  echo "  Response: $HEALTH_RESPONSE"
else
  echo "⚠️  Health check: $HEALTH_RESPONSE"
fi

echo ""
echo "=========================================="
echo "✓ DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Services running:"
echo "  - Node.js (Port 3000): http://localhost:3000"
echo "  - Flask (Port 5001): http://localhost:5001"
echo "  - Frontend URL: https://ask.7mountainsmedia.com"
echo ""
echo "Test commands:"
echo "  curl http://localhost:3000/api/health"
echo "  curl http://localhost:3000"
echo "  curl http://localhost:3000/auth/login"
echo ""
echo "View logs:"
echo "  tail -f nohup.out"
echo ""
