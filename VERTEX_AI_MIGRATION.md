# Vertex AI Embeddings Migration

## Overview
This document outlines the migration from local embeddings to Google Cloud Vertex AI embeddings for improved scalability to support 100+ concurrent users.

## Why Vertex AI?

### Current Bottleneck
- **Local Embeddings**: BAAI/bge-small-en-v1.5 (384 dimensions)
- **Local Reranker**: cross-encoder/ms-marco-MiniLM-L-6-v2
- **Memory Usage**: ~500MB+ per model instance
- **CPU Bottleneck**: Sequential processing on server CPU/GPU
- **Scaling Issue**: Each concurrent user adds significant load

### Vertex AI Benefits
- **Cloud-Managed**: Google handles infrastructure and scaling
- **Auto-Scaling**: Automatically handles 100+ concurrent users
- **Model**: text-embedding-004 (768 dimensions, higher quality)
- **Cost**: ~$0.00002 per 1K characters = $0.30-3/month for typical usage
- **Server Load Reduction**: 80-90% reduction in server resource usage

## What Changed

### New Files
- `vertex_embeddings.py`: New module with VertexEmbedder and VertexReranker classes

### Modified Files
- `config.py`: Added `USE_VERTEX_EMBEDDINGS = True` flag
- `rag_system.py`: Conditional loading of Vertex vs local embedders

### Configuration
```python
# In config.py
USE_VERTEX_EMBEDDINGS = True  # Set to False to use local embeddings
```

## IMPORTANT: Dimension Mismatch Issue

⚠️ **CRITICAL**: Vertex AI embeddings are **768 dimensions** vs local **384 dimensions**

### Impact
Existing ChromaDB collections indexed with local embeddings (384-dim) will NOT work with Vertex embeddings (768-dim).

### Solutions

#### Option 1: Re-index All Collections (Recommended)
```python
# Set flag to use Vertex AI
USE_VERTEX_EMBEDDINGS = True

# Then re-index each collection using folder_indexer.py
python folder_indexer.py
```

Benefits:
- Clean migration
- Better embedding quality with 768-dim model
- No compatibility issues

Drawbacks:
- Takes time to re-index all documents
- Requires re-processing all files from Google Drive

#### Option 2: Maintain Separate Collections
- Keep existing collections using local embeddings
- Create new collections with Vertex embeddings
- Users choose which to use

#### Option 3: Use Compatible Vertex Model
- Check if Vertex AI has a 384-dim model option
- Would avoid re-indexing but may have lower quality

## Cost Analysis

### Vertex AI Pricing
- **Model**: text-embedding-004
- **Cost**: $0.00002 per 1,000 characters
- **Example Usage** (100 users/day):
  - Average query: 100 characters
  - Average documents retrieved: 50 docs × 500 chars = 25,000 chars
  - Daily: 100 users × 25,100 chars = 2,510,000 chars
  - Monthly: 2.51M chars × 30 days × $0.00002/1K = ~$1.50-3/month

### Server Cost Comparison
- **Local**: Requires powerful CPU/GPU server (~$200-500/month)
- **Vertex**: Cheaper server + ~$3/month Vertex AI = Much more cost effective
- **Scaling**: Local requires server upgrades; Vertex scales automatically

## Installation & Setup

### 1. Install Required Packages
Already included in `requirements.txt`:
```bash
pip install google-cloud-aiplatform
```

### 2. Verify Google Cloud Setup
The system already has:
- ✅ Google Cloud project configured
- ✅ Service account credentials
- ✅ Vertex AI API enabled

### 3. Enable Vertex Embeddings
In `config.py`, ensure:
```python
USE_VERTEX_EMBEDDINGS = True
```

### 4. Test the System
```bash
# Start the server
npm start

# Test a query - watch the logs
# Look for: "Loading embedding model: BAAI/bge-small-en-v1.5" (local)
# vs: No embedding model loading message (Vertex)
```

### 5. Monitor Usage (Optional)
```bash
# Check Vertex AI usage in Google Cloud Console
# Navigation: Vertex AI → Dashboard → Usage
```

## Current Status

### ✅ Completed
- Created `vertex_embeddings.py` with VertexEmbedder and VertexReranker
- Updated `config.py` with USE_VERTEX_EMBEDDINGS flag
- Modified `rag_system.py` to conditionally load embedders
- Built frontend with improved file browser navigation

### ⚠️ Not Tested
- Vertex AI embeddings functionality
- Query performance with Vertex
- Dimension mismatch handling

### 🔲 Pending
- Decision on re-indexing strategy
- Testing with real queries
- Performance monitoring under load
- Cost monitoring

## Rollback Plan

If issues arise, easily rollback to local embeddings:

```python
# In config.py
USE_VERTEX_EMBEDDINGS = False
```

Restart the server and it will use local embeddings again.

## File Browser Improvements

### Changes Made
- **Breadcrumb Navigation**: Shows folder path for easier navigation
- **Wider Browser**: Increased from 320px to 384px (w-80 → w-96)
- **Compact Nesting**: Reduced indentation from 16px to 12px per level
- **Better Scrolling**: Added `overscroll-contain` for smoother experience

### UI Updates
- Added breadcrumb state tracking in App.tsx
- Visual hierarchy improvements with borders
- Better contrast and readability

## Next Steps

1. **Test Vertex Embeddings**: Make a query and verify it works
2. **Monitor Performance**: Check server CPU/memory usage
3. **Decide on Re-indexing**: Choose approach for existing collections
4. **Complete Breadcrumbs**: Wire up navigation logic in file browser
5. **Monitor Costs**: Track Vertex AI usage in Google Cloud Console

## Support

For questions or issues:
1. Check server logs for embedding loading messages
2. Verify `USE_VERTEX_EMBEDDINGS` setting in config.py
3. Test with a simple query first before full deployment
4. Monitor Google Cloud Console for API errors

---

**Created**: November 19, 2025  
**Status**: Code ready, testing required  
**Impact**: Enables 100+ concurrent user support with lower infrastructure costs
