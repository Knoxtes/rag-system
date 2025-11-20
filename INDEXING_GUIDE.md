# Document Indexing Guide

## Overview

This guide explains how the document indexing system works in the RAG chat system.

## Architecture

The indexing pipeline consists of several components:

1. **Google Drive Scanner** (`admin_routes.py`)
   - Scans Google Drive folders and files
   - Supports both regular and shared drives
   - Handles pagination for large datasets

2. **Document Loader** (`document_loader.py`)
   - Downloads and extracts text from various file types
   - Supports Google Workspace files (Docs, Sheets, Slides)
   - Supports Microsoft Office files (PDF, DOCX, XLSX, PPTX)
   - Supports text files (TXT, CSV, Markdown)
   - Optional OCR support for images and scanned PDFs

3. **Text Chunker** (`document_loader.py`)
   - Splits documents into semantic chunks
   - Preserves context with overlap
   - Handles special cases (CSV, Excel files)

4. **Embeddings Generator** (`embeddings.py`)
   - Generates vector embeddings using local models
   - Supports caching to avoid recomputation
   - Batch processing for efficiency

5. **Vector Store** (`vector_store.py`)
   - Stores embeddings in ChromaDB
   - Supports multiple collections
   - Efficient batch operations

## Usage

### Starting Indexing

To start the indexing process, make a POST request to the admin endpoint:

```bash
curl -X POST http://localhost:5000/admin/collections/update \
  -H "Content-Type: application/json" \
  -d '{"clear_existing": false}'
```

Parameters:
- `clear_existing` (optional, default: false): If true, clears all existing documents before re-indexing

### Monitoring Progress

Check the indexing status:

```bash
curl http://localhost:5000/admin/collections/status
```

Response includes:
- `running`: Whether indexing is in progress
- `progress`: Percentage complete (0-100)
- `message`: Current status message
- `logs`: Detailed log entries with timestamps
- `stats`: Statistics on files processed and chunks added

## Configuration

### File Type Filtering

The indexer only processes supported file types defined in `admin_routes.py`:

```python
SUPPORTED_MIME_TYPES = {
    # Google Workspace
    'application/vnd.google-apps.document',
    'application/vnd.google-apps.spreadsheet',
    'application/vnd.google-apps.presentation',
    
    # Microsoft Office
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',        # .xlsx
    'application/vnd.openxmlformats-officedocument.presentationml.presentation', # .pptx
    
    # Text files
    'text/plain',
    'text/csv',
}
```

### Limits

- `MAX_FILES_PER_FOLDER`: 1000 (prevents memory issues with large folders)
- `CHUNK_SIZE`: 400 words (configurable in `config.py`)
- `CHUNK_OVERLAP`: 100 words (configurable in `config.py`)
- `EMBEDDING_BATCH_SIZE`: 64 (configurable in `config.py`)

## Features

### Pagination Support

The indexer handles pagination for both folders and files, ensuring all documents are discovered even in large Google Drives.

### Error Handling

- Individual file errors don't stop the entire process
- Detailed error logging for debugging
- Progress continues even if some files fail

### Progress Tracking

- Real-time progress updates (0-100%)
- Detailed logs with timestamps
- Statistics on files processed and chunks added

### Memory Efficiency

- Batch processing for embeddings
- Streaming file downloads
- Limited files per folder to prevent memory exhaustion

### Caching

- Embedding cache to avoid recomputing embeddings for duplicate content
- TTL-based cache expiration
- Disk-based cache for persistence

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure Google Drive credentials are set up (`credentials.json`)
   - Check that token.pickle is valid
   - Solution: Re-authenticate through the admin interface

2. **Out of Memory**
   - Reduce `MAX_FILES_PER_FOLDER`
   - Reduce `EMBEDDING_BATCH_SIZE`
   - Process folders in smaller batches

3. **No Documents Found**
   - Check Google Drive permissions
   - Ensure shared drive access is enabled
   - Verify folder structure

4. **Slow Indexing**
   - Enable embedding cache
   - Increase `EMBEDDING_BATCH_SIZE` (if memory allows)
   - Use more powerful hardware

### Log Interpretation

Logs include the following indicators:

- `✓` : Successful operation
- `⚠️` : Warning (non-critical)
- `✗` : Error (critical)
- `[HH:MM:SS]` : Timestamp

Example log output:

```
[14:23:45] Initializing indexing process...
[14:23:46] ✓ Google Drive authentication successful
[14:23:47] ✓ Embedder initialized
[14:23:48] ✓ Vector store initialized - Current documents: 0
[14:23:48] --- Processing folder: Marketing Documents ---
[14:23:49]   Found 45 files in folder
[14:23:50]   Processing file 1/45: Q1_Report.pdf
[14:23:52]     ✓ Extracted text and created 12 chunks
[14:23:53]     ✓ Added 12 chunks to vector store
```

## Performance

### Expected Performance

- **Small Drive** (< 100 files): 5-10 minutes
- **Medium Drive** (100-1000 files): 30-60 minutes
- **Large Drive** (1000+ files): 1-3 hours

Performance depends on:
- Number and size of documents
- File types (OCR is slower)
- Network speed (for downloads)
- CPU speed (for embeddings)
- Whether embedding cache is warm

### Optimization Tips

1. Enable embedding cache for re-indexing
2. Use batch processing
3. Filter unnecessary file types
4. Process folders selectively
5. Use faster embedding models (at cost of quality)

## Architecture Decisions

### Why Local Embeddings?

- **Free**: No API costs
- **Privacy**: Data never leaves your server
- **Fast**: After initial model download
- **Reliable**: No rate limits or quotas

### Why ChromaDB?

- **Simple**: Easy to set up and use
- **Fast**: Optimized for vector search
- **Flexible**: Supports multiple collections
- **Persistent**: Data survives restarts

### Why Batch Processing?

- **Efficient**: Reduces API calls
- **Memory-safe**: Processes in manageable chunks
- **Resilient**: Individual failures don't stop everything

## Next Steps

After indexing completes:

1. Verify documents were indexed: Check collection stats
2. Test search functionality: Try sample queries
3. Monitor performance: Check query response times
4. Update as needed: Re-index when documents change

## API Reference

### POST /admin/collections/update

Start the indexing process.

**Request Body:**
```json
{
  "clear_existing": false
}
```

**Response:**
```json
{
  "message": "Collection update started",
  "clear_existing": false
}
```

### GET /admin/collections/status

Get current indexing status.

**Response:**
```json
{
  "running": true,
  "progress": 45,
  "message": "Processing folder: Documents (5/10)",
  "started_at": "2025-01-20T14:23:45",
  "logs": [
    "[14:23:45] Initializing indexing process...",
    "[14:23:46] ✓ Google Drive authentication successful"
  ]
}
```
