#!/bin/bash
# Install and build script for Plesk Obsidian Node.js application
# Works with Plesk's managed Node.js environment
# Optimized for: Plesk Obsidian 18.0.74 | AlmaLinux 9.7 | Node.js 22.21.1

echo "🔍 Detecting Plesk Node.js installation..."

# Plesk Obsidian stores Node.js in /opt/plesk/node/
# Find the active Node version set by Plesk (prioritize Node.js 22 for compatibility)
if [ -n "$NODEJS_VERSION" ]; then
    # Plesk sets NODEJS_VERSION environment variable
    NODE_PATH="/opt/plesk/node/$NODEJS_VERSION/bin"
    echo "✅ Using Plesk Node.js $NODEJS_VERSION"
elif [ -d "/opt/plesk/node/22" ]; then
    NODE_PATH="/opt/plesk/node/22/bin"
    echo "✅ Using Plesk Node.js 22"
elif [ -d "/opt/plesk/node/20" ]; then
    NODE_PATH="/opt/plesk/node/20/bin"
    echo "✅ Using Plesk Node.js 20"
elif [ -d "/opt/plesk/node/18" ]; then
    NODE_PATH="/opt/plesk/node/18/bin"
    echo "✅ Using Plesk Node.js 18"
else
    echo "❌ Plesk Node.js not found in /opt/plesk/node/"
    echo "   Please enable Node.js in Plesk for this domain"
    exit 1
fi

# Add to PATH
export PATH="$NODE_PATH:$PATH"

# Verify node works
echo ""
echo "Node version: $($NODE_PATH/node --version)"
echo "NPM version: $($NODE_PATH/npm --version)"

echo ""
echo "📦 Installing dependencies..."
$NODE_PATH/npm install --legacy-peer-deps

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Installation failed"
    exit 1
fi

echo ""
echo "🏗️  Building React app..."
# Use cross-env for environment variables and build directly
GENERATE_SOURCEMAP=false $NODE_PATH/npm run build

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ BUILD SUCCESSFUL!"
    echo "================================================"
    echo "📁 Build output: $(pwd)/build/"
    echo ""
    echo "Next steps:"
    echo "1. Configure Plesk Node.js application:"
    echo "   - Application Root: $(dirname $(pwd))"
    echo "   - Document Root: $(dirname $(pwd))/chat-app/build"
    echo "   - Application Startup File: server.js"
    echo "2. Restart the Node.js application in Plesk"
else
    echo "❌ Build failed"
    exit 1
fi
