#!/bin/bash
# Update dependencies only
# Use this when requirements.txt or package.json changes

APP_ROOT="$(dirname "$(readlink -f "$0")")"

# Detect Plesk Node.js
if [ -f "/opt/plesk/node/18/bin/npm" ]; then
    NPM_CMD="/opt/plesk/node/18/bin/npm"
elif [ -f "/opt/plesk/node/20/bin/npm" ]; then
    NPM_CMD="/opt/plesk/node/20/bin/npm"
elif command -v npm &> /dev/null; then
    NPM_CMD="npm"
else
    echo "❌ npm not found"
    exit 1
fi

echo "📦 Updating dependencies..."
echo ""

# Python dependencies
echo "🐍 Python dependencies..."
python3 -m pip install --user -r "$APP_ROOT/requirements-production.txt"
echo ""

# Node.js dependencies
echo "📦 Node.js dependencies (root)..."
cd "$APP_ROOT" && $NPM_CMD install
echo ""

echo "📦 React dependencies..."
cd "$APP_ROOT/chat-app" && $NPM_CMD install
echo ""

echo "✅ Dependencies updated"
