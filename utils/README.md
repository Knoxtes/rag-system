# Utility Scripts

This directory contains development and maintenance utility scripts for the RAG system.

## Indexing Scripts

- **console_indexer_fixed.py** - Interactive console-based document indexer
- **batch_indexer.py** - Batch process documents for indexing
- **batch_index_all.py** - Index all documents from Google Drive
- **batch_index_selected.py** - Index selected folders/documents
- **live_batch_indexer.py** - Real-time batch indexer with progress monitoring
- **index_all_except_market.py** - Index all collections except marketing
- **reindex_with_vertex.py** - Reindex documents using Vertex AI embeddings

## Cleanup & Maintenance Scripts

- **cleanup_collections.py** - Clean up vector database collections
- **cleanup_only.py** - Perform cleanup without reindexing
- **complete_cleanup_reindex.py** - Full cleanup and reindex operation

## Analysis & Monitoring Scripts

- **check_all_collections.py** - Verify all collections in the database
- **check_sports.py** - Check sports collection specifically
- **get_folder_ids.py** - Retrieve Google Drive folder IDs
- **get_ids.py** - General ID retrieval utility

## Cost Estimation Scripts

- **estimate_cost.py** - Estimate API usage costs
- **actual_cost_estimate.py** - Calculate actual costs based on usage

## Folder Management

- **create_indexed_folders_fixed.py** - Create and manage indexed folder structure

## Usage

These scripts are for development and maintenance purposes only. They are not required for production deployment.

To use any script:
```bash
python utils/script_name.py
```

**Note:** These scripts require additional dependencies that may not be in `requirements-production.txt`. Use the full `requirements.txt` for development.
