#!/bin/bash
# ============================================
# FIX NODE.JS MODULES - COMPLETE REBUILD
# ============================================
# This script completely rebuilds node_modules from scratch

set -e

APP_DIR="/var/www/vhosts/7mountainsmedia.com/ask.7mountainsmedia.com"
PLESK_NODE="/opt/plesk/node/22/bin"

echo "=========================================="
echo "Node.js Module Fix - Complete Rebuild"
echo "=========================================="
echo ""

# Set PATH
export PATH="$PLESK_NODE:$PATH"
cd "$APP_DIR"

echo "[1] Stopping Node.js processes..."
pkill -9 -f "node.*server" || true
sleep 2
echo "✓ Processes stopped"
echo ""

echo "[2] Removing corrupted node_modules and lock files..."
rm -rf node_modules package-lock.json yarn.lock
echo "✓ Old modules removed"
echo ""

echo "[3] Checking npm configuration..."
npm config set legacy-peer-deps true
npm cache clean --force
echo "✓ npm configured"
echo ""

echo "[4] Installing root dependencies from scratch..."
$PLESK_NODE/npm install --omit=dev --legacy-peer-deps --verbose
echo "✓ Dependencies installed"
echo ""

echo "[5] Verifying critical modules..."
echo "Checking express..."
if [ -d "node_modules/express/lib" ]; then
    echo "✓ Express OK: $(ls -la node_modules/express/lib | wc -l) files"
else
    echo "✗ Express lib directory missing!"
    ls -la node_modules/express/ || true
    exit 1
fi

echo "Checking http-proxy-middleware..."
if [ -d "node_modules/http-proxy-middleware" ]; then
    echo "✓ http-proxy-middleware OK"
else
    echo "✗ http-proxy-middleware missing!"
    exit 1
fi
echo ""

echo "[6] Starting Node.js server..."
pkill -9 -f "node.*server" || true
sleep 2

nohup $PLESK_NODE/node server.js > logs/node_server.log 2>&1 &
NODE_PID=$!
sleep 5

if kill -0 $NODE_PID 2>/dev/null; then
    echo "✓ Node.js running (PID: $NODE_PID)"
    echo ""
    echo "[7] Server logs (last 30 lines):"
    tail -30 logs/node_server.log
else
    echo "✗ Node.js failed to start"
    echo ""
    echo "Error logs:"
    tail -50 logs/node_server.log
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ DEPLOYMENT COMPLETE"
echo "=========================================="
echo "Node.js server is running on port 3000"
echo "Flask backend is running on port 5001"
echo ""
echo "Test the deployment:"
echo "  curl http://ask.7mountainsmedia.com/api/health"
echo "  curl http://ask.7mountainsmedia.com"
