#!/bin/bash

# RAG System - Production Frontend Rebuild Script
# This script rebuilds the React frontend with production configuration
# and restarts the Node.js server to serve the new build

set -e

echo "=========================================="
echo "RAG System - Frontend Rebuild (Production)"
echo "=========================================="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "[*] Script directory: $SCRIPT_DIR"
echo ""

# Path to Plesk Node.js
PLESK_NODE="/opt/plesk/node/22/bin"
export PATH="$PLESK_NODE:$PATH"

echo "[1] Verifying Node.js and npm..."
NODE_VERSION=$($PLESK_NODE/node --version)
NPM_VERSION=$($PLESK_NODE/npm --version)
echo "✓ Node.js: $NODE_VERSION"
echo "✓ npm: $NPM_VERSION"
echo ""

echo "[2] Pulling latest changes from git..."
cd "$SCRIPT_DIR"
git pull origin main
echo "✓ Git pull completed"
echo ""

echo "[3] Installing frontend dependencies..."
cd "$SCRIPT_DIR/chat-app"
$PLESK_NODE/npm install --legacy-peer-deps --prefer-offline
echo "✓ Frontend dependencies installed"
echo ""

echo "[4] Building React frontend..."
echo "   (This may take 2-3 minutes...)"
export NODE_OPTIONS='--max-old-space-size=4096'
export GENERATE_SOURCEMAP=false
export REACT_APP_API_BASE_URL=''
$PLESK_NODE/npm run build
BUILD_EXIT_CODE=$?

if [ $BUILD_EXIT_CODE -ne 0 ]; then
  echo "❌ Build failed with exit code $BUILD_EXIT_CODE"
  exit 1
fi
echo "✓ React build completed successfully"
echo ""

echo "[5] Stopping Node.js server..."
pkill -f "node server.js" || true
sleep 2
echo "✓ Node.js server stopped"
echo ""

echo "[6] Restarting Node.js server..."
cd "$SCRIPT_DIR"
nohup $PLESK_NODE/node server.js > nohup.out 2>&1 &
NODE_PID=$!
sleep 3

if kill -0 $NODE_PID 2>/dev/null; then
  echo "✓ Node.js server restarted (PID: $NODE_PID)"
else
  echo "❌ Failed to start Node.js server"
  tail -20 nohup.out
  exit 1
fi
echo ""

echo "[7] Verifying deployment..."
sleep 2

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:3000/api/health || echo '{}')
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
  echo "✓ Health check passed"
else
  echo "⚠️  Health check response: $HEALTH_RESPONSE"
fi

# Check if build was served
BUILD_CHECK=$(curl -s http://localhost:3000/ | grep -c "main\." || echo "0")
if [ "$BUILD_CHECK" -gt 0 ]; then
  echo "✓ React build is being served"
else
  echo "⚠️  Could not verify React build is being served"
fi

echo ""
echo "=========================================="
echo "✓ REBUILD COMPLETE"
echo "=========================================="
echo ""
echo "Frontend has been rebuilt and redeployed."
echo "Server: http://localhost:3000"
echo ""
echo "Test endpoints:"
echo "  curl http://localhost:3000/api/health"
echo "  curl http://localhost:3000"
echo ""
