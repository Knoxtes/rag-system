#!/bin/bash
# Production Startup Script for RAG System
# This script performs pre-flight checks and starts the application

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}RAG System - Production Startup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}✗ Error: .env file not found${NC}"
    echo -e "${YELLOW}  Please create .env file with required variables${NC}"
    exit 1
fi

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo -e "${RED}✗ Error: credentials.json not found${NC}"
    echo -e "${YELLOW}  Please add Google Cloud credentials${NC}"
    exit 1
fi

# Check if React build exists
if [ ! -d "chat-app/build" ]; then
    echo -e "${YELLOW}⚠ Warning: React build not found${NC}"
    echo -e "${YELLOW}  Running npm run build...${NC}"
    npm run build
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠ Warning: Node modules not found${NC}"
    echo -e "${YELLOW}  Running npm install...${NC}"
    npm install
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Load environment variables
source .env 2>/dev/null || true

# Display configuration
echo -e "${GREEN}✓ Configuration loaded${NC}"
echo -e "  Environment: ${FLASK_ENV:-development}"
echo -e "  Debug Mode: ${DEBUG:-True}"
echo -e "  Allowed Domains: ${ALLOWED_DOMAINS:-not set}"
echo ""

# Check production requirements
if [ "${FLASK_ENV}" = "production" ]; then
    echo -e "${GREEN}✓ Production mode detected${NC}"
    
    # Check if secret keys are set
    if [[ "${FLASK_SECRET_KEY}" == *"change-this"* ]] || [[ "${JWT_SECRET_KEY}" == *"change-this"* ]]; then
        echo -e "${RED}✗ Error: Default secret keys detected${NC}"
        echo -e "${YELLOW}  Please update FLASK_SECRET_KEY and JWT_SECRET_KEY in .env${NC}"
        echo -e "${YELLOW}  Generate with: python -c 'import secrets; print(secrets.token_hex(32))'${NC}"
        exit 1
    fi
    
    # Check if OAuth redirect URI is localhost
    if [[ "${OAUTH_REDIRECT_URI}" == *"localhost"* ]]; then
        echo -e "${YELLOW}⚠ Warning: OAuth redirect URI points to localhost${NC}"
        echo -e "${YELLOW}  Update OAUTH_REDIRECT_URI in .env for production${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Running in development mode${NC}"
    echo -e "${YELLOW}  Set FLASK_ENV=production in .env for production${NC}"
fi

echo ""
echo -e "${GREEN}✓ Pre-flight checks complete${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}Starting RAG System...${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Start the application
exec npm start
