# Files to Remove/Archive

## Redundant Documentation (Keep only PLESK_DEPLOYMENT_GUIDE.md)
- [ ] PLESK_DEPLOYMENT.md (outdated, replaced by PLESK_DEPLOYMENT_GUIDE.md)
- [ ] PLESK_MANUAL_SETUP.md (outdated, replaced by PLESK_DEPLOYMENT_GUIDE.md)
- [ ] START_HERE.md (outdated, now in README.md)
- [ ] DEPLOY_NOW.md (outdated, now in PLESK_DEPLOYMENT_GUIDE.md)
- [ ] PRODUCTION_READY.md (outdated, now in README.md)
- [ ] PRODUCTION_CHECKLIST.md (outdated, now in PLESK_DEPLOYMENT_GUIDE.md)

## Obsolete Deployment Scripts
- [ ] deploy.sh (replaced by deploy-plesk.sh)
- [ ] deploy.bat (Windows version, not needed for Plesk/Linux)
- [ ] start-production.sh (replaced by npm start + Plesk management)
- [ ] start-production.bat (Windows version, not needed)
- [ ] start-flexible.sh (not used in Plesk deployment)
- [ ] start-flexible.bat (Windows version, not needed)
- [ ] setup-server.sh (functionality now in deploy-plesk.sh)
- [ ] rebuild-frontend.sh (functionality in chat-app/install-and-build.sh)
- [ ] update-dependencies.sh (replaced by deploy-plesk.sh)

## Old Indexer Scripts (Superseded by console_indexer_fixed.py)
- [ ] console_indexer.py (old version)
- [ ] batch_indexer.py (old version)
- [ ] batch_index_selected.py (old version)
- [ ] batch_index_all.py (functionality in console_indexer_fixed.py)
- [ ] index_all_except_market.py (specific use case, can archive)
- [ ] reindex_with_vertex.py (specific use case, can archive)

## Database Management Scripts (Keep only if needed for maintenance)
- [ ] check_sports.py (one-time check script)
- [ ] check_all_collections.py (one-time check script)
- [ ] cleanup_collections.py (one-time cleanup script)
- [ ] cleanup_only.py (one-time cleanup script)
- [ ] complete_cleanup_reindex.py (one-time cleanup script)
- [ ] analyze_chromadb.py (one-time analysis script)
- [ ] cleanup_chromadb.py (one-time cleanup script)

## Utility Scripts (Archive if not actively used)
- [ ] get_ids.py (utility for getting Drive IDs)
- [ ] get_folder_ids.py (utility for getting folder IDs)
- [ ] create_indexed_folders.py (old version)
- [ ] create_indexed_folders_fixed.py (fixed version, might still need)
- [ ] estimate_cost.py (cost estimation utility)
- [ ] actual_cost_estimate.py (cost estimation utility)

## Testing Scripts
- [ ] test_cache.py (development testing)
- [ ] test_optimizations.py (development testing)

## Old App Entry Points (Keep only chat_api.py + server.js)
- [ ] app.py (old entry point, replaced by chat_api.py)

## Development Documentation (Can move to docs/ folder)
- [ ] IMPLEMENTATION_SUMMARY.md
- [ ] OPTIMIZATIONS_COMPLETE.md
- [ ] OPTIMIZATION_GUIDE.md
- [ ] FIXES_APPLIED.md
- [ ] INDEXER_FIXES_APPLIED.md
- [ ] FULL_INDEXING_GUIDE.md
- [ ] REINDEX_QUICK_GUIDE.md
- [ ] SAFE_DATABASE_CLEAR.md

## Action Plan

### 1. Archive Development Docs
```bash
mkdir -p docs/archive/development
mv IMPLEMENTATION_SUMMARY.md docs/archive/development/
mv OPTIMIZATIONS_COMPLETE.md docs/archive/development/
mv OPTIMIZATION_GUIDE.md docs/archive/development/
mv FIXES_APPLIED.md docs/archive/development/
mv INDEXER_FIXES_APPLIED.md docs/archive/development/
mv FULL_INDEXING_GUIDE.md docs/archive/development/
mv REINDEX_QUICK_GUIDE.md docs/archive/development/
mv SAFE_DATABASE_CLEAR.md docs/archive/development/
```

### 2. Archive Obsolete Deployment Docs
```bash
mkdir -p docs/archive/obsolete-deployment
mv PLESK_DEPLOYMENT.md docs/archive/obsolete-deployment/
mv PLESK_MANUAL_SETUP.md docs/archive/obsolete-deployment/
mv START_HERE.md docs/archive/obsolete-deployment/
mv DEPLOY_NOW.md docs/archive/obsolete-deployment/
mv PRODUCTION_READY.md docs/archive/obsolete-deployment/
mv PRODUCTION_CHECKLIST.md docs/archive/obsolete-deployment/
```

### 3. Archive Old Scripts
```bash
mkdir -p docs/archive/old-scripts
mv deploy.sh docs/archive/old-scripts/
mv deploy.bat docs/archive/old-scripts/
mv start-production.sh docs/archive/old-scripts/
mv start-production.bat docs/archive/old-scripts/
mv start-flexible.sh docs/archive/old-scripts/
mv start-flexible.bat docs/archive/old-scripts/
mv setup-server.sh docs/archive/old-scripts/
mv rebuild-frontend.sh docs/archive/old-scripts/
mv update-dependencies.sh docs/archive/old-scripts/
```

### 4. Archive Old Indexers
```bash
mkdir -p docs/archive/old-indexers
mv console_indexer.py docs/archive/old-indexers/
mv batch_indexer.py docs/archive/old-indexers/
mv batch_index_selected.py docs/archive/old-indexers/
mv batch_index_all.py docs/archive/old-indexers/
```

### 5. Archive Cleanup Scripts
```bash
mkdir -p docs/archive/cleanup-scripts
mv check_sports.py docs/archive/cleanup-scripts/
mv check_all_collections.py docs/archive/cleanup-scripts/
mv cleanup_collections.py docs/archive/cleanup-scripts/
mv cleanup_only.py docs/archive/cleanup-scripts/
mv complete_cleanup_reindex.py docs/archive/cleanup-scripts/
mv analyze_chromadb.py docs/archive/cleanup-scripts/
mv cleanup_chromadb.py docs/archive/cleanup-scripts/
```

### 6. Keep These Files (Production Critical)

**Core Application:**
- server.js
- chat_api.py
- rag_system.py
- config.py
- auth.py
- oauth_config.py
- auth_routes.py
- admin_routes.py
- admin_auth.py
- google_drive_oauth.py

**Core Utilities:**
- vector_store.py
- vertex_embeddings.py
- embeddings.py
- embedding_cache.py
- document_loader.py
- documentai_ocr.py
- connection_pool.py
- rate_limiter.py
- redis_cache.py
- semantic_cache.py
- response_compression.py
- answer_logger.py
- system_stats.py

**Active Indexers:**
- console_indexer_fixed.py
- live_batch_indexer.py

**Production Deployment:**
- deploy-plesk.sh
- update-from-git.sh
- package.json
- requirements-production.txt
- passenger_wsgi.py (for Passenger/WSGI if needed)

**Documentation (Keep):**
- README.md (updated)
- PLESK_DEPLOYMENT_GUIDE.md (new, comprehensive)
- VERTEX_AI_MIGRATION.md
- DOCUMENTAI_SETUP.md
- .env.example

**Other Keep:**
- .gitignore
- verify_production.py
- create_deployment_package.py (if used)
- cleanup_obsolete_files.py (this script itself)

## Automated Cleanup Script

Run this to execute the archiving:

```bash
chmod +x cleanup-project.sh
./cleanup-project.sh
```

This will:
1. Create docs/archive/ structure
2. Move obsolete files to appropriate archive folders
3. Leave git history intact
4. Generate a summary report

## After Cleanup

Your project structure will be:
```
rag-system/
├── server.js
├── chat_api.py
├── rag_system.py
├── config.py
├── [core Python files]
├── deploy-plesk.sh
├── update-from-git.sh
├── package.json
├── requirements-production.txt
├── README.md
├── PLESK_DEPLOYMENT_GUIDE.md
├── .env.example
├── .gitignore
├── chat-app/
├── docs/
│   └── archive/
│       ├── development/
│       ├── obsolete-deployment/
│       ├── old-scripts/
│       ├── old-indexers/
│       └── cleanup-scripts/
└── [essential files only]
```

This creates a clean, production-focused repository optimized for Plesk deployment.
