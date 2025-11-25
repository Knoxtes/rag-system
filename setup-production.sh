#!/bin/bash
# ============================================
# PLESK PRODUCTION SETUP SCRIPT
# ============================================
# This script sets up the RAG system for production on Plesk

set -e

APP_DIR="/var/www/vhosts/7mountainsmedia.com/ask.7mountainsmedia.com"
DOMAIN="ask.7mountainsmedia.com"
PLESK_NODE="/opt/plesk/node/22/bin"

echo "=========================================="
echo "RAG System Production Setup"
echo "=========================================="
echo "Domain: $DOMAIN"
echo "App Directory: $APP_DIR"
echo ""

# 1. Ensure Node.js is in PATH
echo "[1] Configuring Node.js PATH..."
export PATH="$PLESK_NODE:$PATH"
node_version=$($PLESK_NODE/node --version)
npm_version=$($PLESK_NODE/npm --version)
echo "✓ Node.js: $node_version"
echo "✓ npm: $npm_version"
echo ""

# 2. Stop any running processes
echo "[2] Stopping existing services..."
pkill -9 -f "node.*server.js" || true
pkill -9 -f "python.*chat_api" || true
sleep 2
echo "✓ Services stopped"
echo ""

# 3. Install root Node.js dependencies
echo "[3] Installing root Node.js dependencies..."
cd "$APP_DIR"
export PATH="$PLESK_NODE:$PATH"
$PLESK_NODE/npm install --omit=dev --legacy-peer-deps
echo "✓ Root dependencies installed"
echo ""

# 3b. Rebuild React frontend
echo "[3b] Building React frontend..."
cd "$APP_DIR/chat-app"
$PLESK_NODE/npm install --omit=dev --legacy-peer-deps
$PLESK_NODE/npm run build
echo "✓ React build completed"
echo ""

# 4. Setup Python virtual environment
echo "[4] Setting up Python environment..."
cd "$APP_DIR"
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements-production.txt
echo "✓ Python environment ready"
echo ""

# 5. Test Flask startup
echo "[5] Testing Flask backend..."
nohup python3 chat_api.py --port 5001 > logs/flask_api.log 2>&1 &
FLASK_PID=$!
sleep 5

# Check if Flask is running
if kill -0 $FLASK_PID 2>/dev/null; then
    echo "✓ Flask running (PID: $FLASK_PID)"
else
    echo "✗ Flask failed to start. Checking logs..."
    tail -n 30 logs/flask_api.log
    exit 1
fi
echo ""

# 6. Start Node.js server with Passenger
echo "[6] Starting Node.js server..."
export PATH="$PLESK_NODE:$PATH"
export NODE_ENV=production
export FLASK_ENV=production
export PORT=3000
export FLASK_PORT=5001

# Kill old Node process if exists
pkill -9 -f "node.*server.js" || true
sleep 2

# Start Node.js
nohup $PLESK_NODE/node server.js > logs/node_server.log 2>&1 &
NODE_PID=$!
sleep 5

if kill -0 $NODE_PID 2>/dev/null; then
    echo "✓ Node.js running (PID: $NODE_PID)"
else
    echo "✗ Node.js failed to start. Checking logs..."
    tail -n 30 logs/node_server.log
    exit 1
fi
echo ""

# 7. Verify health checks
echo "[7] Health checks..."
sleep 3

echo "✓ Application Setup Complete!"
echo ""
echo "=========================================="
echo "Service Status:"
echo "=========================================="
echo ""

# Check Flask
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo "✓ Flask Backend:    http://localhost:5001/health"
else
    echo "✗ Flask Backend:    Not responding"
fi

# Check Node.js
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Node.js Server:   http://localhost:3000"
else
    echo "✗ Node.js Server:   Not responding"
fi

echo ""
echo "=========================================="
echo "Application URLs:"
echo "=========================================="
echo "Public:  https://$DOMAIN"
echo "API:     https://$DOMAIN/api"
echo ""
echo "Log Files:"
echo "  Node.js: $APP_DIR/logs/node_server.log"
echo "  Flask:   $APP_DIR/logs/flask_api.log"
echo "=========================================="
