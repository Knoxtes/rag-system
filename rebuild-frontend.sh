#!/bin/bash
# Rebuild React frontend only
# Use this when you make frontend changes

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

echo "🏗️  Rebuilding React frontend..."
cd "$APP_ROOT/chat-app" && $NPM_CMD run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend rebuilt successfully"
    echo "📍 Build location: $APP_ROOT/chat-app/build"
else
    echo "❌ Build failed"
    exit 1
fi
