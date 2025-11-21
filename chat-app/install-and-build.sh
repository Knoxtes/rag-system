#!/bin/bash
# Install script for Plesk with nodenv
# This script finds and uses the available Node version

echo "🔍 Detecting Node.js..."

# Try to find node in nodenv
if [ -d "$HOME/.nodenv/versions/25" ]; then
    export PATH="$HOME/.nodenv/versions/25/bin:$PATH"
    echo "✅ Using nodenv Node 25"
elif [ -d "$HOME/.nodenv/versions/22" ]; then
    export PATH="$HOME/.nodenv/versions/22/bin:$PATH"
    echo "✅ Using nodenv Node 22"
else
    echo "❌ Node not found in nodenv"
    exit 1
fi

# Verify node works
node --version
npm --version

echo ""
echo "📦 Installing dependencies with --ignore-scripts..."
npm install --ignore-scripts

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Installation failed"
    exit 1
fi

echo ""
echo "🏗️  Building React app..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "📁 Build output: ./build/"
else
    echo "❌ Build failed"
    exit 1
fi
