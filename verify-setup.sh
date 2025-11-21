#!/bin/bash

# RAG System Setup Verification Script
# Checks if all required components are properly configured

echo "🔍 RAG System Setup Verification"
echo "================================="
echo ""

ERRORS=0
WARNINGS=0

# Check Node.js
echo "📦 Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d'v' -f2 | cut -d'.' -f1)
    echo "   ✅ Node.js $NODE_VERSION installed"
    
    if [ "$NODE_MAJOR" -lt 25 ]; then
        echo "   ⚠️  Warning: Node.js 25.2.0+ recommended for production"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "   ❌ Node.js not found"
    ERRORS=$((ERRORS + 1))
fi

# Check npm
echo ""
echo "📦 Checking npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "   ✅ npm $NPM_VERSION installed"
else
    echo "   ❌ npm not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Python
echo ""
echo "🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ $PYTHON_VERSION installed"
else
    echo "   ❌ Python 3 not found"
    ERRORS=$((ERRORS + 1))
fi

# Check pip
echo ""
echo "📦 Checking pip..."
if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version)
    else
        PIP_VERSION=$(pip --version)
    fi
    echo "   ✅ $PIP_VERSION"
else
    echo "   ❌ pip not found"
    ERRORS=$((ERRORS + 1))
fi

# Check required files
echo ""
echo "📄 Checking required files..."

if [ -f "credentials.json" ]; then
    echo "   ✅ credentials.json found"
else
    echo "   ❌ credentials.json missing"
    echo "      Upload your Google Cloud service account credentials"
    ERRORS=$((ERRORS + 1))
fi

if [ -f ".env" ]; then
    echo "   ✅ .env file found"
else
    echo "   ⚠️  .env file missing"
    echo "      Copy .env.example to .env and configure"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -f "package.json" ]; then
    echo "   ✅ package.json found"
else
    echo "   ❌ package.json missing"
    ERRORS=$((ERRORS + 1))
fi

if [ -f "requirements-production.txt" ]; then
    echo "   ✅ requirements-production.txt found"
else
    echo "   ❌ requirements-production.txt missing"
    ERRORS=$((ERRORS + 1))
fi

# Check directories
echo ""
echo "📁 Checking directories..."

if [ -d "chat-app" ]; then
    echo "   ✅ chat-app directory found"
else
    echo "   ❌ chat-app directory missing"
    ERRORS=$((ERRORS + 1))
fi

if [ -d "chat-app/build" ]; then
    echo "   ✅ chat-app/build directory found"
else
    echo "   ⚠️  chat-app/build directory missing"
    echo "      Run: npm run build"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -d "logs" ]; then
    echo "   ✅ logs directory found"
else
    echo "   ⚠️  logs directory missing"
    echo "      Will be created automatically"
    WARNINGS=$((WARNINGS + 1))
fi

# Check Node dependencies
echo ""
echo "📦 Checking Node.js dependencies..."
if [ -d "node_modules" ]; then
    echo "   ✅ Root node_modules found"
else
    echo "   ⚠️  Root node_modules missing"
    echo "      Run: npm install"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -d "chat-app/node_modules" ]; then
    echo "   ✅ Frontend node_modules found"
else
    echo "   ⚠️  Frontend node_modules missing"
    echo "      Run: cd chat-app && npm install"
    WARNINGS=$((WARNINGS + 1))
fi

# Check Python packages (basic check)
echo ""
echo "🐍 Checking Python packages..."
if python3 -c "import flask" 2>/dev/null; then
    echo "   ✅ Flask installed"
else
    echo "   ⚠️  Flask not installed"
    echo "      Run: pip3 install -r requirements-production.txt"
    WARNINGS=$((WARNINGS + 1))
fi

if python3 -c "import chromadb" 2>/dev/null; then
    echo "   ✅ ChromaDB installed"
else
    echo "   ⚠️  ChromaDB not installed"
    echo "      Run: pip3 install -r requirements-production.txt"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "================================="
echo "📊 Verification Summary"
echo "================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed!"
    echo ""
    echo "🚀 Ready to deploy! Run:"
    echo "   npm start"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Setup has $WARNINGS warning(s)"
    echo ""
    echo "   Your setup will likely work, but review warnings above."
    echo ""
    echo "🚀 To deploy anyway, run:"
    echo "   npm start"
    exit 0
else
    echo "❌ Setup has $ERRORS error(s) and $WARNINGS warning(s)"
    echo ""
    echo "   Please fix the errors above before deploying."
    echo ""
    echo "📖 See PLESK_SETUP_GUIDE.md for detailed instructions"
    exit 1
fi
