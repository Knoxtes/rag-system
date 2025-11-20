# Complete Database Rebuild Guide

## Overview
You can now completely rebuild your RAG system database through the admin portal, indexing all folders from the 7MM Resources shared drive automatically.

## Prerequisites
1. **Google Drive Authentication**: Connect to Google Drive in admin portal
2. **Cloud Packages**: Install google-cloud-aiplatform and google-cloud-documentai
3. **Vertex AI Configured**: Set `USE_VERTEX_EMBEDDINGS = True` in config.py
4. **Document AI Configured**: Set processor details in config.py

## Complete Workflow

### Step 1: Access Admin Dashboard
```
http://your-domain/admin/dashboard
```
Log in with admin credentials.

### Step 2: Install Cloud Packages (One-Time)
1. Navigate to **Cloud Migration Center**
2. Click **"Install Cloud Packages"** button
3. Wait for installation (2-5 minutes)
4. Verify status shows "Installed"

### Step 3: Clear Database
1. In Cloud Migration Center, find **"Clear Database"** card
2. Click **"Clear Database"** button
3. Confirm the warning dialog
4. Monitor progress in the logs section below
5. Wait for completion (~30 seconds)

### Step 4: Index All Folders
1. In Cloud Migration Center, find **"Index All Folders"** card
2. Click **"Index All Folders"** button
3. Confirm the dialog
4. Monitor real-time progress:
   - Folder-by-folder status
   - File counts per folder
   - Progress percentage (10-95%)
5. Watch for completion message

**Expected Duration**: 10-30 minutes depending on folder count and file sizes

### Step 5: Restart Server
After indexing completes:
```powershell
# Stop current server
Stop-Process -Name python -Force

# Start fresh
python app.py
```

## What Gets Indexed

### Folder Discovery
- Queries 7MM Resources shared drive ID: `0AMjLFg-ngmOAUk9PVA`
- Finds ALL folders automatically
- No manual configuration needed

### Per-Folder Processing
- **Collection Name**: `folder_{folder_id}`
- **File Limit**: First 50 files per folder (performance)
- **Supported Types**: PDF, DOCX, TXT, CSV, XLSX, PPTX
- **OCR**: Document AI for PDFs, EasyOCR fallback

### Metadata Saved
- Folder name
- Folder ID
- File count
- Last indexed timestamp

## Progress Monitoring

### Status Display
```
15% - Processing folder: Q1 Reports (3/20 folders)
42% - Processing folder: Marketing Materials (8/20 folders)
95% - Finalizing collections (20/20 folders)
✅ Complete! Restart server.
```

### Live Logs
```
• Discovered 20 folders from 7MM Resources
• Creating collection: folder_abc123 (Q1 Reports)
• Indexed 15 files from folder: Q1 Reports
• Creating collection: folder_def456 (Marketing Materials)
• Indexed 32 files from folder: Marketing Materials
...
• All folders indexed successfully!
• Saved indexed_folders.json
```

## Troubleshooting

### Issue: "Google Drive not connected"
**Solution**: 
1. Go to Google Drive tab in admin dashboard
2. Click "Connect to Google Drive"
3. Complete OAuth flow
4. Try indexing again

### Issue: "No folders found"
**Solution**:
1. Verify shared drive ID in `chat_api.py`
2. Check Google Drive permissions
3. Ensure account has access to 7MM Resources

### Issue: "Package not found"
**Solution**:
1. Click "Install Cloud Packages" in admin portal
2. Wait for installation
3. Verify green checkmark appears
4. Try indexing again

### Issue: Indexing stops mid-process
**Solution**:
1. Check server logs for errors
2. Verify API quotas not exceeded
3. Check file permissions on problematic files
4. Re-run indexing (resumes automatically)

## Performance Notes

### File Limits
- **Per Folder**: 50 files indexed initially
- **Why Limited**: Prevents timeout on large folders
- **To Increase**: Modify `run_full_indexing_process()` line with `max_files` parameter

### API Rate Limits
- **Document AI**: 60 requests/minute (watch quotas)
- **Vertex AI**: 60 requests/minute per project
- **Google Drive**: 10,000 requests/100 seconds

### Optimization Tips
1. **Schedule During Off-Hours**: Less API contention
2. **Monitor Quotas**: Check GCP console during indexing
3. **Batch Folders**: Index high-priority folders first
4. **Cache Enabled**: Embeddings cached automatically

## Cost Estimates

### Document AI OCR
- **Price**: ~$1.50 per 1,000 pages
- **Example**: 100 PDFs × 10 pages = 1,000 pages = $1.50

### Vertex AI Embeddings
- **Price**: ~$0.025 per 1,000 characters
- **Example**: 1,000 documents × 2,000 chars = 2M chars = $50

### Total Estimate
- **Small Deployment**: 500 files ≈ $10-20
- **Medium Deployment**: 2,000 files ≈ $50-75
- **Large Deployment**: 10,000 files ≈ $200-300

## Verification

### Check Collections
After restart, verify collections:
```python
from vector_store import VectorStore
vs = VectorStore()
print(vs.list_collections())
```

### Check indexed_folders.json
```powershell
Get-Content indexed_folders.json | ConvertFrom-Json
```

### Test Query
Go to chat interface, ask:
```
"What's in the Q1 Reports folder?"
```

## Next Steps

### After Successful Indexing
1. ✅ Restart server
2. ✅ Test queries in chat interface
3. ✅ Verify all folders appear in dropdown
4. ✅ Check Document AI usage in GCP console
5. ✅ Monitor response quality

### Maintenance
- **Weekly**: Check for new folders, re-index if needed
- **Monthly**: Review API costs and quotas
- **Quarterly**: Full reindex with latest embeddings

## Advanced: Manual Indexing

If you need more control:

```python
from rag_system import RAGSystem

# Index specific folder
rag = RAGSystem(collection_name="my_collection")
rag.index_drive_folder(
    folder_id="abc123",
    folder_name="Custom Folder",
    max_files=100
)
```

## Support

**Issues?** Check:
1. Server logs: `logs/chat_system.log`
2. Migration logs in admin portal
3. GCP console for API errors
4. indexed_folders.json for collection list

**Documentation:**
- Vertex AI Guide: `/static/VERTEX_AI_MIGRATION.md`
- Document AI Guide: `/static/DOCUMENTAI_SETUP.md`
- This Guide: `FULL_INDEXING_GUIDE.md`
