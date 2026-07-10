# RAG System - Incremental Indexing Architecture

## Overview

This document describes the incremental document indexing system that enables efficient, cost-effective document digestion for the RAG Chat application.

## Key Benefits

| Feature | Benefit |
|---------|---------|
| **Incremental Sync** | Only processes new/changed files (~90% cost savings) |
| **File Tracking** | SQLite database tracks file states persistently |
| **Scheduled Jobs** | Automatic midnight sync (configurable) |
| **Deletion Detection** | Removes orphaned documents from vector store |
| **Batch Processing** | Efficient embedding generation |
| **Admin API** | REST endpoints for monitoring and control |

## Components

### 1. File Tracker (`file_tracker.py`)

SQLite-based persistent tracking of document states:

```python
from file_tracker import FileTracker

tracker = FileTracker("./file_tracker.db")

# Check if file needs processing
needs_update, reason = tracker.check_file_needs_update(
    file_id="abc123",
    modified_time="2025-01-15T10:30:00Z"
)
# Returns: (True, "new") | (True, "modified") | (False, "up_to_date")

# Update after successful indexing
tracker.update_file_state(
    file_id="abc123",
    file_name="report.pdf",
    modified_time="2025-01-15T10:30:00Z",
    chunk_count=15,
    content_hash="md5hash"
)

# Get statistics
stats = tracker.get_stats()
# {'total_files': 1500, 'total_chunks': 25000, 'files_by_folder': {...}}
```

**Database Schema:**
- `tracked_files` - File states (ID, name, modified_time, hash, chunks)
- `sync_history` - Audit log of all sync operations

### 2. Incremental Indexer (`incremental_indexer.py`)

Intelligent document processing that:
- Scans configured Google Drive folders
- Compares file states with tracker database
- Only processes new or modified files
- Detects and removes deleted files
- Batches embeddings for efficiency

**Usage:**
```bash
# Show current status
python incremental_indexer.py --status

# Run full incremental sync
python incremental_indexer.py --sync

# Preview changes (dry run)
python incremental_indexer.py --dry-run

# Sync specific folder
python incremental_indexer.py --folder <folder_id>
```

### 3. Scheduler (`scheduler.py`)

Automated document digestion:

**For Cron/Plesk (Recommended):**
```bash
# Add to crontab - runs at midnight UTC
0 0 * * * cd /path/to/rag-system && python scheduler.py --once
```

**As Daemon (Alternative):**
```bash
# Run continuously, syncing at configured time
python scheduler.py --time 00:00
```

**Commands:**
```bash
# Run once and exit (for cron)
python scheduler.py --once

# Show last run info
python scheduler.py --status

# Run at specific time (daemon mode)
python scheduler.py --time 02:30
```

### 4. Admin API (`admin_sync_routes.py`)

REST endpoints for sync management:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/sync/status` | GET | Current sync status & tracker stats |
| `/admin/sync/start` | POST | Start incremental sync |
| `/admin/sync/history` | GET | Sync operation history |
| `/admin/sync/files` | GET | List tracked files |
| `/admin/sync/file/<id>` | GET | Single file state |
| `/admin/sync/file/<id>/reindex` | POST | Force reindex file |
| `/admin/sync/schedule` | GET | Scheduled sync info |

## Sync Process Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    INCREMENTAL SYNC                          │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Load Configured    │
                   │  Folders            │
                   └─────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  For Each Folder:             │
              │  - Scan all files recursively │
              │  - Get file metadata          │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  For Each File:               │
              │  - Check tracker database     │
              │  - Compare modified_time      │
              └───────────────────────────────┘
                    │                    │
            ┌───────┴───────┐    ┌───────┴───────┐
            │  Up-to-date   │    │  New/Modified │
            └───────────────┘    └───────────────┘
                    │                    │
            ┌───────┴───────┐    ┌───────┴───────┐
            │  Skip         │    │  Process:     │
            │  (mark        │    │  - Extract    │
            │   checked)    │    │  - Chunk      │
            └───────────────┘    │  - Embed      │
                                 │  - Store      │
                                 └───────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────┐
                          │  Update Tracker Database │
                          └──────────────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────┐
                          │  Detect Deleted Files    │
                          │  (in tracker but not     │
                          │   seen in scan)          │
                          └──────────────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────┐
                          │  Remove from Vector      │
                          │  Store & Tracker         │
                          └──────────────────────────┘
```

## Cost Analysis

### Before (Full Re-index)
- 1,000 documents × 10 chunks × $0.00002/embedding = $0.20/sync
- Daily sync = $6/month

### After (Incremental)
- First sync: Full cost ($0.20)
- Subsequent syncs: ~5% file change rate
- 50 files × 10 chunks × $0.00002 = $0.01/sync
- Daily sync = $0.30/month

**Savings: ~95%**

## Configuration

### Environment Variables

```bash
# Sync time (HH:MM in UTC)
SYNC_TIME=00:00

# Webhook for notifications (optional)
SYNC_WEBHOOK_URL=https://hooks.slack.com/...

# Embeddings (use Vertex AI for production)
USE_VERTEX_AI=true
USE_VERTEX_EMBEDDINGS=true

# Batch size for processing
EMBEDDING_BATCH_SIZE=64
```

### Tracked Folders

Configured in `indexed_folders.json`:
```json
{
  "folder_id_1": {
    "name": "Company Documents",
    "location": "Shared Drive",
    "indexed_at": "2025-01-15T00:00:00"
  }
}
```

## Monitoring

### Check Sync Status
```bash
python scheduler.py --status
python incremental_indexer.py --status
```

### View Logs
```bash
tail -f logs/scheduler.log
tail -f logs/incremental_indexer.log
```

### API Health
```bash
curl https://yourdomain.com/admin/sync/status
```

## Troubleshooting

### Sync Not Running
1. Check cron is configured correctly
2. Verify Python path in cron command
3. Check logs/scheduler.log for errors

### Files Not Being Indexed
1. Check file is in supported MIME types
2. Verify folder is in indexed_folders.json
3. Check logs/incremental_indexer.log

### Force Re-index Specific File
```bash
# Via API
curl -X POST https://yourdomain.com/admin/sync/file/<file_id>/reindex

# Via Python
from file_tracker import FileTracker
tracker = FileTracker()
tracker.remove_file("file_id")  # Will be re-indexed on next sync
```

### Reset All Tracking
```bash
# Delete tracker database (will re-index everything)
rm file_tracker.db

# Run sync
python incremental_indexer.py --sync
```
