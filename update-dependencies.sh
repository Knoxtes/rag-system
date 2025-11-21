#!/bin/bash
# Update dependencies only
# Use this when requirements.txt or package.json changes

APP_ROOT="$(dirname "$(readlink -f "$0")")"

echo "📦 Updating dependencies..."
echo ""

# Python dependencies
echo "🐍 Python dependencies..."
python3 -m pip install --user -r "$APP_ROOT/requirements-production.txt"
echo ""

# Node.js dependencies
echo "📦 Node.js dependencies (root)..."
npm install --prefix "$APP_ROOT"
echo ""

echo "📦 React dependencies..."
npm install --prefix "$APP_ROOT/chat-app"
echo ""

echo "✅ Dependencies updated"
