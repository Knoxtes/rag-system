# Deprecated Scripts

The following scripts are redundant or have been consolidated. They are kept for reference but should not be used in production:

## Indexing Scripts (Consolidated)

### Deprecated:
- `console_indexer.py` - Original version (30KB)
  - **Reason**: Superseded by console_indexer_fixed.py
  - **Use instead**: console_indexer_fixed.py

### Active:
- `console_indexer_fixed.py` - Fixed version used by batch indexers
- `batch_indexer.py` - Batch indexing utility
- `live_batch_indexer.py` - Live batch indexing
- `batch_index_all.py` - Index all collections
- `batch_index_selected.py` - Index selected collections

## Cleanup Scripts (Consolidated)

### Deprecated:
- `cleanup_only.py` - Simple cleanup (2.8KB)
  - **Reason**: Limited functionality, use complete_cleanup_reindex.py instead
  
### Active:
- `cleanup_collections.py` - Clean specific collections
- `complete_cleanup_reindex.py` - Full cleanup and reindex

## Setup Scripts (Consolidated)

### Deprecated:
- `setup-server.sh` - Generic server setup
  - **Reason**: Replaced by setup-plesk.sh for AlmaLinux/Plesk
  
- `deploy.sh` - Generic deployment
  - **Reason**: Superseded by setup-plesk.sh with Plesk-specific optimizations

### Active:
- `setup-plesk.sh` - **Recommended** - Plesk Obsidian 18.0.73 on AlmaLinux 9.7
- `rebuild-frontend.sh` - Frontend rebuild utility
- `update-dependencies.sh` - Dependency update utility

## Deployment Scripts

### Windows Scripts (Keep for Windows users):
- `deploy.bat` - Windows deployment
- `start-flexible.bat` - Windows startup

### Linux Scripts:
- `start-flexible.sh` - Flexible startup script
- `deploy.sh` - Generic deployment (use setup-plesk.sh instead for Plesk)

## Requirements Files (Consolidated)

### Deprecated:
- `requirements.txt` - Bloated (343 lines, Windows-specific paths)
  - **Reason**: Contains Windows paths, TTS dependencies, development tools
  - **Size**: ~257 packages, many unnecessary for production

### Active:
- `requirements-linux.txt` - **Recommended** - Clean Linux dependencies (70 packages)
- `requirements-production.txt` - Production optimized (56 packages)
- `requirements-auth.txt` - Authentication only
- `chat-api-requirements.txt` - Minimal API requirements

## Recommendation

For Plesk Obsidian 18.0.73 on AlmaLinux 9.7:
1. Use `setup-plesk.sh` for deployment
2. Use `requirements-linux.txt` for Python dependencies
3. Use `console_indexer_fixed.py` via batch scripts for indexing
4. Use `complete_cleanup_reindex.py` for maintenance

## Removal Plan

These scripts will be removed in a future version once all dependencies are verified:
- `console_indexer.py` (redundant)
- `cleanup_only.py` (limited functionality)
- `setup-server.sh` (superseded)
- `requirements.txt` (bloated, use requirements-linux.txt)
