#!/bin/bash
# ============================================================================
# Project Cleanup Script
# Archives obsolete files to docs/archive/
# ============================================================================

set -e

echo "🧹 RAG System Project Cleanup"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Create archive directories
print_info "Creating archive structure..."
mkdir -p docs/archive/development
mkdir -p docs/archive/obsolete-deployment
mkdir -p docs/archive/old-scripts
mkdir -p docs/archive/old-indexers
mkdir -p docs/archive/cleanup-scripts
mkdir -p docs/archive/test-scripts

print_status "Archive directories created"

# Function to move file if it exists
move_if_exists() {
    local file=$1
    local dest=$2
    if [ -f "$file" ]; then
        mv "$file" "$dest/"
        echo "  📦 Moved: $file"
    fi
}

# Archive development documentation
echo ""
print_info "Archiving development documentation..."
move_if_exists "IMPLEMENTATION_SUMMARY.md" "docs/archive/development"
move_if_exists "OPTIMIZATIONS_COMPLETE.md" "docs/archive/development"
move_if_exists "OPTIMIZATION_GUIDE.md" "docs/archive/development"
move_if_exists "FIXES_APPLIED.md" "docs/archive/development"
move_if_exists "INDEXER_FIXES_APPLIED.md" "docs/archive/development"
move_if_exists "FULL_INDEXING_GUIDE.md" "docs/archive/development"
move_if_exists "REINDEX_QUICK_GUIDE.md" "docs/archive/development"
move_if_exists "SAFE_DATABASE_CLEAR.md" "docs/archive/development"

# Archive obsolete deployment docs
echo ""
print_info "Archiving obsolete deployment documentation..."
move_if_exists "PLESK_DEPLOYMENT.md" "docs/archive/obsolete-deployment"
move_if_exists "PLESK_MANUAL_SETUP.md" "docs/archive/obsolete-deployment"
move_if_exists "START_HERE.md" "docs/archive/obsolete-deployment"
move_if_exists "DEPLOY_NOW.md" "docs/archive/obsolete-deployment"
move_if_exists "PRODUCTION_READY.md" "docs/archive/obsolete-deployment"
move_if_exists "PRODUCTION_CHECKLIST.md" "docs/archive/obsolete-deployment"

# Archive old scripts
echo ""
print_info "Archiving old deployment scripts..."
move_if_exists "deploy.sh" "docs/archive/old-scripts"
move_if_exists "deploy.bat" "docs/archive/old-scripts"
move_if_exists "start-production.sh" "docs/archive/old-scripts"
move_if_exists "start-production.bat" "docs/archive/old-scripts"
move_if_exists "start-flexible.sh" "docs/archive/old-scripts"
move_if_exists "start-flexible.bat" "docs/archive/old-scripts"
move_if_exists "setup-server.sh" "docs/archive/old-scripts"
move_if_exists "rebuild-frontend.sh" "docs/archive/old-scripts"
move_if_exists "update-dependencies.sh" "docs/archive/old-scripts"

# Archive old indexers
echo ""
print_info "Archiving old indexer scripts..."
move_if_exists "console_indexer.py" "docs/archive/old-indexers"
move_if_exists "batch_indexer.py" "docs/archive/old-indexers"
move_if_exists "batch_index_selected.py" "docs/archive/old-indexers"
move_if_exists "batch_index_all.py" "docs/archive/old-indexers"
move_if_exists "index_all_except_market.py" "docs/archive/old-indexers"
move_if_exists "reindex_with_vertex.py" "docs/archive/old-indexers"

# Archive cleanup scripts
echo ""
print_info "Archiving one-time cleanup scripts..."
move_if_exists "check_sports.py" "docs/archive/cleanup-scripts"
move_if_exists "check_all_collections.py" "docs/archive/cleanup-scripts"
move_if_exists "cleanup_collections.py" "docs/archive/cleanup-scripts"
move_if_exists "cleanup_only.py" "docs/archive/cleanup-scripts"
move_if_exists "complete_cleanup_reindex.py" "docs/archive/cleanup-scripts"
move_if_exists "analyze_chromadb.py" "docs/archive/cleanup-scripts"
move_if_exists "cleanup_chromadb.py" "docs/archive/cleanup-scripts"

# Archive test scripts
echo ""
print_info "Archiving test scripts..."
move_if_exists "test_cache.py" "docs/archive/test-scripts"
move_if_exists "test_optimizations.py" "docs/archive/test-scripts"

# Archive old app entry point
echo ""
print_info "Archiving old app entry point..."
move_if_exists "app.py" "docs/archive/old-scripts"

# Create archive README
echo ""
print_info "Creating archive README..."
cat > docs/archive/README.md << 'EOF'
# Archived Files

This directory contains files that were part of the development process but are no longer needed for production deployment.

## Directory Structure

- **development/** - Development documentation and guides
- **obsolete-deployment/** - Outdated deployment documentation
- **old-scripts/** - Obsolete deployment and startup scripts
- **old-indexers/** - Previous versions of indexing scripts
- **cleanup-scripts/** - One-time database cleanup utilities
- **test-scripts/** - Development testing scripts

## Why Archived?

These files were archived to:
1. Simplify the project structure
2. Focus on production-ready deployment
3. Reduce confusion with multiple similar files
4. Maintain git history while cleaning up the working directory

## Current Production Files

See the root directory for:
- **README.md** - Main documentation
- **PLESK_DEPLOYMENT_GUIDE.md** - Complete deployment guide
- **deploy-plesk.sh** - Automated deployment script
- **server.js** - Node.js entry point
- **chat_api.py** - Flask backend

## Archived On

November 21, 2025

## Git History

All these files remain in git history. To restore a file:
```bash
git checkout HEAD -- path/to/file
```
EOF

print_status "Archive README created"

# Generate summary
echo ""
echo "================================================"
echo "📊 Cleanup Summary"
echo "================================================"
echo ""

TOTAL_ARCHIVED=$(find docs/archive -type f -not -name "README.md" | wc -l)
print_status "Total files archived: $TOTAL_ARCHIVED"

echo ""
print_info "Archived by category:"
echo "  📚 Development docs: $(ls docs/archive/development 2>/dev/null | wc -l)"
echo "  📋 Obsolete deployment docs: $(ls docs/archive/obsolete-deployment 2>/dev/null | wc -l)"
echo "  🔧 Old scripts: $(ls docs/archive/old-scripts 2>/dev/null | wc -l)"
echo "  🗃️  Old indexers: $(ls docs/archive/old-indexers 2>/dev/null | wc -l)"
echo "  🧹 Cleanup scripts: $(ls docs/archive/cleanup-scripts 2>/dev/null | wc -l)"
echo "  🧪 Test scripts: $(ls docs/archive/test-scripts 2>/dev/null | wc -l)"

echo ""
print_info "Production files remain in root directory"
print_info "Git history preserved for all archived files"

echo ""
echo "================================================"
print_status "Cleanup complete!"
echo "================================================"
echo ""
print_info "Your project is now optimized for Plesk deployment"
print_info "See README.md and PLESK_DEPLOYMENT_GUIDE.md for next steps"
echo ""
