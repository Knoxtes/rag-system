# Safe Database Clear & Reindex Process

## ⚠️ Important: ChromaDB File Locking Issue

**Problem:** ChromaDB keeps database files locked while the server is running. You **cannot** clear the database through the web UI while the server is active.

**Solution:** Use the CLI tool with the server stopped.

## Recommended Workflow

### Step 1: Stop the Server
```powershell
# Press Ctrl+C in the terminal running the server
# Or find and kill the process:
Get-Process python | Stop-Process -Force
```

### Step 2: Clear Database (CLI)
```powershell
# With backup (recommended)
python reindex_with_vertex.py --backup

# Without backup (faster, but no safety net)
python reindex_with_vertex.py --no-backup

# Just backup, don't clear
python reindex_with_vertex.py --backup-only
```

**What this does:**
- ✅ Creates timestamped backup in `./chroma_db_backups/`
- ✅ Safely deletes all ChromaDB files
- ✅ Removes the lock
- ✅ Prepares for fresh indexing

### Step 3: Start Server
```powershell
python app.py
```

### Step 4: Index All Folders (Web UI)
Now you can use the admin portal:

1. Go to: `http://localhost:5000/admin/dashboard`
2. Navigate to **Cloud Migration Center**
3. Click **"Index All Folders"**
4. Monitor progress in real-time
5. Wait for completion (~10-30 minutes)

### Step 5: Restart Server (Final)
```powershell
# Stop server (Ctrl+C)
# Restart
python app.py
```

All collections now loaded with 768-dim Vertex AI embeddings! ✅

## Why This Happens

### File Locking Explained
```
Server Running:
├── ChromaDB Connection Open
│   ├── data_level0.bin [LOCKED]
│   ├── index.bin [LOCKED]
│   └── sqlite.db [LOCKED]
└── Cannot Delete Files ❌

Server Stopped:
├── No Connections
│   ├── data_level0.bin [FREE]
│   ├── index.bin [FREE]
│   └── sqlite.db [FREE]
└── Can Delete Files ✅
```

### Windows File Locking
Windows locks files more aggressively than Linux/Mac:
- **Linux/Mac**: Can delete while open (marked for deletion)
- **Windows**: Cannot delete while open (hard lock)

This is why the error shows:
```
[WinError 32] The process cannot access the file because 
it is being used by another process
```

## Alternative: Force Close & Clear

If you need to clear via web UI (not recommended):

### Option A: Close ChromaDB Connections First
```python
# Add to admin_routes.py before clearing
from vector_store import VectorStore
vs = VectorStore()
if hasattr(vs, 'client'):
    vs.client = None
import gc
gc.collect()
```

**Issue:** Other parts of the app may still hold references.

### Option B: Subprocess CLI Call
```python
# In admin_routes.py, instead of shutil.rmtree():
import subprocess
subprocess.run([
    sys.executable, 
    'reindex_with_vertex.py', 
    '--backup'
], check=True)
```

**Issue:** Runs in same process, same locks exist.

### Option C: Scheduled Shutdown
```python
# Set flag, clear on next startup
with open('.clear_db_flag', 'w') as f:
    f.write('true')
return jsonify({'message': 'Database will clear on next restart'})
```

**Issue:** Requires code changes to check flag on startup.

## Best Practice: Use CLI Tool

The `reindex_with_vertex.py` tool was designed specifically for this:

```python
# reindex_with_vertex.py benefits:
✅ Runs independently
✅ No ChromaDB connections
✅ Proper error handling
✅ Backup verification
✅ Progress display
✅ Safe for Windows file locking
```

## Troubleshooting

### Error: "Failed to fetch"
**Cause:** Endpoint doesn't exist or auth token expired

**Solution:**
```javascript
// Check browser console
// Verify token exists:
localStorage.getItem('authToken')
// If null, log in again
```

### Error: "WinError 32"
**Cause:** Server still running, files locked

**Solution:**
```powershell
# Verify no Python processes
Get-Process python

# Force kill if needed
Get-Process python | Stop-Process -Force

# Then clear
python reindex_with_vertex.py --backup
```

### Error: "Permission denied"
**Cause:** File permissions or antivirus

**Solution:**
```powershell
# Run PowerShell as Administrator
# Temporarily disable antivirus
# Check folder permissions
```

### Error: "Backup failed"
**Cause:** Insufficient disk space

**Solution:**
```powershell
# Check space
Get-PSDrive C

# Clear old backups
Remove-Item ./chroma_db_backups/backup_* -Recurse -Force

# Try again
python reindex_with_vertex.py --backup
```

## Quick Reference

| Task | Command | Server State |
|------|---------|--------------|
| Backup only | `python reindex_with_vertex.py --backup-only` | Can run |
| Clear only | `python reindex_with_vertex.py --skip-backup` | Must stop |
| Backup + Clear | `python reindex_with_vertex.py` | Must stop |
| Index folders | Use Web UI | Must run |
| Check status | Use Web UI | Must run |

## Future Improvements

### Planned Solutions:
1. **Graceful Shutdown API**: Add endpoint to stop server, clear DB, restart
2. **Startup Flag Check**: Detect `.clear_db_flag` and clear before loading DB
3. **Connection Pool Management**: Close all ChromaDB connections before clear
4. **Process Isolation**: Spawn separate process to clear DB

### Current Workaround:
✅ **Use CLI tool** - fastest and safest solution for now

## Summary

**The admin portal "Clear Database" button will fail if server is running.**

**Correct workflow:**
1. Stop server (Ctrl+C)
2. Run CLI: `python reindex_with_vertex.py --backup`
3. Start server: `python app.py`
4. Use web UI: Click "Index All Folders"
5. Restart server when done

This ensures no file locking issues and safe database migration. 🎯
