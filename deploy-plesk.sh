#!/bin/bash
# ============================================================================
# Plesk Deployment Script for Ask.7MountainsMedia.com
# Optimized for: Plesk Obsidian 18.0.74 | AlmaLinux 9.7 | Node.js 22.21.1
# ============================================================================

set -e  # Exit on error

echo "🚀 RAG System - Plesk Deployment Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect Plesk Node.js path (prioritize Node.js 22 for compatibility)
PLESK_NODE_22="/opt/plesk/node/22/bin"
PLESK_NODE_20="/opt/plesk/node/20/bin"
PLESK_NODE_18="/opt/plesk/node/18/bin"

if [ -d "$PLESK_NODE_22" ]; then
    NODE_PATH="$PLESK_NODE_22"
    NODE_VERSION="22.x"
elif [ -d "$PLESK_NODE_20" ]; then
    NODE_PATH="$PLESK_NODE_20"
    NODE_VERSION="20.x"
elif [ -d "$PLESK_NODE_18" ]; then
    NODE_PATH="$PLESK_NODE_18"
    NODE_VERSION="18.x"
else
    NODE_PATH=$(dirname $(which node) 2>/dev/null || echo "")
    NODE_VERSION=$(node --version 2>/dev/null || echo "unknown")
fi

echo -e "${BLUE}📌 Detected Node.js:${NC} $NODE_VERSION at $NODE_PATH"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC}  $1"
}

# Check if we're in the right directory
if [ ! -f "server.js" ]; then
    print_error "server.js not found. Please run this script from the project root."
    exit 1
fi

print_status "Located project root"

# Step 1: Pull latest changes from git
echo ""
echo "📦 Step 1: Updating from Git repository..."
echo "-------------------------------------------"
if git rev-parse --git-dir > /dev/null 2>&1; then
    print_info "Fetching latest changes..."
    git fetch origin
    git reset --hard origin/feature/easyocr-integration
    print_status "Repository updated to latest commit"
else
    print_warning "Not a git repository. Skipping git update."
fi

# Step 2: Check Python dependencies
echo ""
echo "🐍 Step 2: Installing Python dependencies..."
echo "-------------------------------------------"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.9+"
    exit 1
fi

print_info "Using Python: $($PYTHON_CMD --version)"

if [ -f "requirements-production.txt" ]; then
    print_info "Installing production dependencies..."
    $PYTHON_CMD -m pip install --upgrade pip --quiet
    $PYTHON_CMD -m pip install -r requirements-production.txt --quiet
    print_status "Python dependencies installed"
else
    print_error "requirements-production.txt not found"
    exit 1
fi

# Step 3: Install Node.js dependencies
echo ""
echo "📦 Step 3: Installing Node.js dependencies..."
echo "-------------------------------------------"

if [ -n "$NODE_PATH" ] && [ -d "$NODE_PATH" ]; then
    export PATH="$NODE_PATH:$PATH"
fi

print_info "Installing root dependencies..."
npm install --quiet
print_status "Root dependencies installed"

# Step 4: Build React frontend
echo ""
echo "⚛️  Step 4: Building React frontend..."
echo "-------------------------------------------"

cd chat-app

if [ -f "install-and-build.sh" ]; then
    chmod +x install-and-build.sh
    print_info "Running optimized build script..."
    ./install-and-build.sh
else
    print_info "Running standard build..."
    npm install --legacy-peer-deps --quiet
    npm run build
fi

if [ -d "build" ] && [ -f "build/index.html" ]; then
    print_status "React build completed successfully"
    BUILD_SIZE=$(du -sh build | cut -f1)
    print_info "Build size: $BUILD_SIZE"
else
    print_error "React build failed - build directory not found"
    exit 1
fi

cd ..

# Step 5: Create logs directory
echo ""
echo "📝 Step 5: Setting up logs directory..."
echo "-------------------------------------------"
mkdir -p logs
chmod 755 logs
print_status "Logs directory ready"

# Step 6: Verify critical files
echo ""
echo "🔍 Step 6: Verifying critical files..."
echo "-------------------------------------------"

MISSING_FILES=()

if [ ! -f ".env" ]; then
    MISSING_FILES+=(".env")
fi

if [ ! -f "credentials.json" ]; then
    MISSING_FILES+=("credentials.json")
fi

if [ ! -f "server.js" ]; then
    MISSING_FILES+=("server.js")
fi

if [ ! -f "chat_api.py" ]; then
    MISSING_FILES+=("chat_api.py")
fi

if [ ${#MISSING_FILES[@]} -eq 0 ]; then
    print_status "All critical files present"
else
    print_error "Missing critical files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    print_info "Please upload missing files before starting the application"
fi

# Step 7: Check environment configuration
echo ""
echo "⚙️  Step 7: Checking environment configuration..."
echo "-------------------------------------------"

if [ -f ".env" ]; then
    if grep -q "CHANGE-THIS" .env; then
        print_warning ".env file contains default values - please update:"
        echo "   - FLASK_SECRET_KEY"
        echo "   - JWT_SECRET_KEY"
    else
        print_status "Environment configuration looks good"
    fi
    
    if grep -q "Ask.7MountainsMedia.com" .env; then
        print_status "Production domain configured"
    else
        print_warning "OAUTH_REDIRECT_URI may need updating to Ask.7MountainsMedia.com"
    fi
else
    print_warning ".env file not found - copy from .env.example"
fi

# Step 8: Final summary
echo ""
echo "=" "================================================"
echo "🎉 Deployment preparation complete!"
echo "================================================"
echo ""
print_info "Next steps:"
echo "   1. Upload missing files (if any listed above)"
echo "   2. Update .env with production values"
echo "   3. Set environment variables in Plesk:"
echo "      Domains → Ask.7MountainsMedia.com → Node.js → Environment Variables"
echo "   4. Restart application in Plesk:"
echo "      Domains → Ask.7MountainsMedia.com → Node.js → Restart App"
echo ""
echo "   5. Verify deployment:"
echo "      https://Ask.7MountainsMedia.com/api/health"
echo ""
print_status "Deployment script completed successfully!"
echo ""
