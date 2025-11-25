#!/bin/bash
# ============================================================================
# Quick Update Script for ask.7mountainsmedia.com
# Use this script to quickly pull and deploy updates from Git
# ============================================================================

set -e

echo "🔄 Quick Update - RAG System"
echo "============================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC}  $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

# Pull latest changes
print_info "Pulling latest changes from Git..."
git fetch origin
git reset --hard origin/feature/easyocr-integration

print_status "Repository updated"

# Check what changed
if git diff --name-only HEAD@{1} HEAD | grep -q "requirements"; then
    print_warning "Python dependencies changed - run: pip install -r requirements-production.txt"
fi

if git diff --name-only HEAD@{1} HEAD | grep -q "package.json"; then
    print_warning "Node dependencies changed - run: npm install"
fi

if git diff --name-only HEAD@{1} HEAD | grep -q "chat-app/src"; then
    print_warning "Frontend changed - rebuild with: cd chat-app && ./install-and-build.sh"
fi

echo ""
print_status "Update complete!"
print_info "Restart application in Plesk to apply changes"
echo ""
