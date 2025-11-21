#!/bin/bash
# Server Setup Script for RAG System
# Run this after cloning the repo on your Plesk server

echo "================================================"
echo "RAG System - Server Setup"
echo "================================================"
echo ""

# Get the script directory (application root)
APP_ROOT="$(dirname "$(readlink -f "$0")")"
echo "📁 Application Root: $APP_ROOT"
echo ""

# Detect Plesk Node.js
if [ -f "/opt/plesk/node/18/bin/npm" ]; then
    NPM_CMD="/opt/plesk/node/18/bin/npm"
elif [ -f "/opt/plesk/node/20/bin/npm" ]; then
    NPM_CMD="/opt/plesk/node/20/bin/npm"
elif command -v npm &> /dev/null; then
    NPM_CMD="npm"
else
    echo "❌ npm not found. Please install Node.js or use Plesk Node.js interface."
    echo "   Try: /opt/plesk/node/*/bin/npm"
    exit 1
fi
echo "📦 Using npm: $NPM_CMD"
echo ""

# 1. Install Python dependencies
echo "🐍 Installing Python dependencies..."
python3 -m pip install --user -r "$APP_ROOT/requirements-production.txt"
if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
echo ""

# 2. Install root Node.js dependencies
echo "📦 Installing Node.js dependencies (root)..."
cd "$APP_ROOT" && $NPM_CMD install
if [ $? -eq 0 ]; then
    echo "✅ Root dependencies installed"
else
    echo "❌ Failed to install root dependencies"
    exit 1
fi
echo ""

# 3. Install React app dependencies
echo "📦 Installing React app dependencies..."
cd "$APP_ROOT/chat-app" && $NPM_CMD install
if [ $? -eq 0 ]; then
    echo "✅ React dependencies installed"
else
    echo "❌ Failed to install React dependencies"
    exit 1
fi
echo ""

# 4. Build React app
echo "🏗️  Building React production app..."
cd "$APP_ROOT/chat-app" && $NPM_CMD run build
if [ $? -eq 0 ]; then
    echo "✅ React app built successfully"
else
    echo "❌ Failed to build React app"
    exit 1
fi
echo ""

# 5. Create logs directory
echo "📂 Creating logs directory..."
mkdir -p "$APP_ROOT/logs"
echo "✅ Logs directory created"
echo ""

# 6. Check for required files
echo "🔍 Checking required files..."
REQUIRED_FILES=(".env" "credentials.json" "token.pickle" "indexed_folders.json")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$APP_ROOT/$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    echo "✅ All required files present"
else
    echo "⚠️  Missing files (you'll need to upload these):"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
fi
echo ""

# 7. Summary
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Upload missing files if any (credentials.json, token.pickle, etc.)"
echo "2. Upload chroma_db/ folder (520 MB) via SFTP"
echo "3. Update .env with production URLs:"
echo "   - OAUTH_REDIRECT_URI=https://chat.7mountainsmedia.com/auth/callback"
echo "   - CORS_ORIGINS=https://chat.7mountainsmedia.com"
echo "4. Configure Plesk Node.js settings:"
echo "   - Application Root: $APP_ROOT"
echo "   - Document Root: $APP_ROOT/chat-app/build"
echo "   - Application Startup File: server.js"
echo "   - Node.js Version: 18.x or 20.x (NOT 25.x)"
echo "5. Add environment variables in Plesk"
echo "6. Restart the Node.js application"
echo ""
echo "To verify: Visit https://chat.7mountainsmedia.com/api/health"
echo ""
