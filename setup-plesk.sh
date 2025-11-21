#!/bin/bash
# ===========================================
# RAG System - Plesk Setup Script
# Optimized for Plesk Obsidian 18.0.73 on AlmaLinux 9.7
# Domain: Ask.7MountainsMedia.com
# ===========================================

set -e  # Exit on error

echo "================================================"
echo "🚀 RAG System - Plesk Deployment Setup"
echo "================================================"
echo ""
echo "📍 Target: Ask.7MountainsMedia.com"
echo "🖥️  Platform: Plesk Obsidian 18.0.73 + AlmaLinux 9.7"
echo ""

# Get application root
APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Application Root: $APP_ROOT"
echo ""

# Check if running on Plesk server
if [ ! -d "/opt/plesk" ]; then
    echo "⚠️  Warning: Plesk directory not detected. Are you on a Plesk server?"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ============================================
# Step 1: Detect Node.js Installation
# ============================================
echo "📦 Step 1: Detecting Node.js..."

NPM_CMD=""
NODE_CMD=""

# Check for Plesk Node.js installations (prefer 22.x)
if [ -f "/opt/plesk/node/22/bin/npm" ]; then
    NPM_CMD="/opt/plesk/node/22/bin/npm"
    NODE_CMD="/opt/plesk/node/22/bin/node"
    echo "✅ Found Plesk Node.js 22.x"
elif [ -f "/opt/plesk/node/20/bin/npm" ]; then
    NPM_CMD="/opt/plesk/node/20/bin/npm"
    NODE_CMD="/opt/plesk/node/20/bin/node"
    echo "✅ Found Plesk Node.js 20.x"
elif [ -f "/opt/plesk/node/18/bin/npm" ]; then
    NPM_CMD="/opt/plesk/node/18/bin/npm"
    NODE_CMD="/opt/plesk/node/18/bin/node"
    echo "✅ Found Plesk Node.js 18.x"
elif command -v npm &> /dev/null; then
    NPM_CMD="npm"
    NODE_CMD="node"
    echo "✅ Found system Node.js: $(node --version)"
else
    echo "❌ Error: npm not found. Please install Node.js via Plesk or system package manager."
    echo "   For Plesk: Enable Node.js in Domains → Your Domain → Node.js"
    exit 1
fi

echo "   Using: $NPM_CMD"
echo "   Version: $($NODE_CMD --version)"
echo ""

# ============================================
# Step 2: Install Python Dependencies
# ============================================
echo "🐍 Step 2: Installing Python dependencies..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $PYTHON_VERSION"

# Install from requirements-linux.txt (clean Linux dependencies)
if [ -f "$APP_ROOT/requirements-linux.txt" ]; then
    echo "   Installing from requirements-linux.txt..."
    python3 -m pip install --user -r "$APP_ROOT/requirements-linux.txt" --quiet
    if [ $? -eq 0 ]; then
        echo "✅ Python dependencies installed successfully"
    else
        echo "❌ Failed to install Python dependencies"
        echo "   Trying requirements-production.txt as fallback..."
        python3 -m pip install --user -r "$APP_ROOT/requirements-production.txt"
    fi
else
    echo "   Installing from requirements-production.txt..."
    python3 -m pip install --user -r "$APP_ROOT/requirements-production.txt"
    if [ $? -eq 0 ]; then
        echo "✅ Python dependencies installed successfully"
    else
        echo "❌ Failed to install Python dependencies"
        exit 1
    fi
fi
echo ""

# ============================================
# Step 3: Install Root Node.js Dependencies
# ============================================
echo "📦 Step 3: Installing root Node.js dependencies..."
cd "$APP_ROOT"
$NPM_CMD install --quiet
if [ $? -eq 0 ]; then
    echo "✅ Root dependencies installed"
else
    echo "❌ Failed to install root dependencies"
    exit 1
fi
echo ""

# ============================================
# Step 4: Install React App Dependencies
# ============================================
echo "⚛️  Step 4: Installing React app dependencies..."
cd "$APP_ROOT/chat-app"
$NPM_CMD install --quiet
if [ $? -eq 0 ]; then
    echo "✅ React dependencies installed"
else
    echo "❌ Failed to install React dependencies"
    exit 1
fi
echo ""

# ============================================
# Step 5: Build React Production App
# ============================================
echo "🏗️  Step 5: Building React production app..."
cd "$APP_ROOT/chat-app"
$NPM_CMD run build
if [ $? -eq 0 ]; then
    echo "✅ React app built successfully"
    echo "   Build location: $APP_ROOT/chat-app/build/"
else
    echo "❌ Failed to build React app"
    echo ""
    echo "If you see localStorage errors, this is a Node.js 25.x bug."
    echo "Solution: Use Node.js 22.x or 20.x in Plesk Node.js settings."
    exit 1
fi
echo ""

# ============================================
# Step 6: Create Required Directories
# ============================================
echo "📂 Step 6: Creating required directories..."

mkdir -p "$APP_ROOT/logs"
mkdir -p "$APP_ROOT/tmp"
mkdir -p "$APP_ROOT/chroma_db"

chmod 755 "$APP_ROOT/logs"
chmod 755 "$APP_ROOT/tmp"
chmod 755 "$APP_ROOT/chroma_db"

echo "✅ Directories created:"
echo "   - logs/ (application logs)"
echo "   - tmp/ (temporary files)"
echo "   - chroma_db/ (vector database)"
echo ""

# ============================================
# Step 7: Check Required Files
# ============================================
echo "🔍 Step 7: Checking required files..."

REQUIRED_FILES=("credentials.json" "token.pickle" ".env")
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
    echo ""
    echo "📝 Required file templates:"
    echo ""
    echo "1. credentials.json - Google Cloud service account JSON"
    echo "2. token.pickle - Google OAuth token (auto-generated on first auth)"
    echo "3. .env - Environment configuration (see PLESK_ALMALINUX_SETUP.md)"
    echo ""
fi
echo ""

# ============================================
# Step 8: Generate Secret Keys
# ============================================
echo "🔑 Step 8: Generating secret keys..."
echo ""
echo "Add these to your .env file:"
echo ""
python3 -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
echo ""

# ============================================
# Step 9: Summary & Next Steps
# ============================================
echo "================================================"
echo "✅ Setup Complete!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Upload Missing Files (if any):"
if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo "   Via Plesk File Manager or SFTP, upload to: $APP_ROOT"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
else
    echo "   ✅ All files present"
fi
echo ""

echo "2. Configure .env File:"
echo "   Edit $APP_ROOT/.env with:"
echo "   - DOMAIN=Ask.7MountainsMedia.com"
echo "   - CORS_ORIGINS=https://Ask.7MountainsMedia.com"
echo "   - OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback"
echo "   - Add generated secret keys from above"
echo ""

echo "3. Configure Plesk Node.js App:"
echo "   Go to: Domains → Ask.7MountainsMedia.com → Node.js"
echo "   - Enable Node.js"
echo "   - Node.js Version: 22.x (recommended)"
echo "   - Application Mode: production"
echo "   - Application Root: $APP_ROOT"
echo "   - Document Root: $APP_ROOT/chat-app/build"
echo "   - Application Startup File: server.js"
echo ""

echo "4. Add Environment Variables in Plesk:"
echo "   FLASK_ENV=production"
echo "   NODE_ENV=production"
echo "   PORT=3000"
echo "   FLASK_PORT=5001"
echo "   (Copy other values from .env)"
echo ""

echo "5. Upload Vector Database (if migrating):"
echo "   SFTP upload chroma_db/ folder to: $APP_ROOT/chroma_db/"
echo ""

echo "6. Restart Application:"
echo "   In Plesk Node.js settings, click 'Restart App'"
echo ""

echo "7. Verify Deployment:"
echo "   Health check: https://Ask.7MountainsMedia.com/api/health"
echo "   Frontend: https://Ask.7MountainsMedia.com"
echo ""

echo "================================================"
echo "📖 Full Documentation:"
echo "   See PLESK_ALMALINUX_SETUP.md for detailed guide"
echo "================================================"
echo ""
