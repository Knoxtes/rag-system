#!/bin/bash
# Rebuild React frontend only
# Use this when you make frontend changes

APP_ROOT="$(dirname "$(readlink -f "$0")")"

echo "🏗️  Rebuilding React frontend..."
npm run build --prefix "$APP_ROOT/chat-app"

if [ $? -eq 0 ]; then
    echo "✅ Frontend rebuilt successfully"
    echo "📍 Build location: $APP_ROOT/chat-app/build"
else
    echo "❌ Build failed"
    exit 1
fi
