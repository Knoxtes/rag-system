# Quick Guide: Reindex with Vertex AI Embeddings

## 🚀 Fast Track (Recommended)

```powershell
# 1. Run the reindex script
python reindex_with_vertex.py

# 2. When prompted, type: yes

# 3. Stop your current server (Ctrl+C if running)

# 4. Restart the server
npm start

# 5. Access your web app and use collections normally
# The system will automatically reindex with Vertex AI
```

## 📋 What This Does

1. **Backs up** your current database to `chroma_db_backups/backup_TIMESTAMP/`
2. **Clears** the `./chroma_db` directory completely
3. **Verifies** Vertex AI configuration is correct
4. **Prepares** system for fresh indexing with 768-dimensional embeddings

## 🎯 Alternative Commands

### Just create a backup (no clearing)
```powershell
python reindex_with_vertex.py --backup-only
```

### Backup and clear (but don't reindex yet)
```powershell
python reindex_with_vertex.py --clear-only
```

### Skip backup (NOT recommended!)
```powershell
python reindex_with_vertex.py --skip-backup
```

## ✅ Verification Steps

After restarting the server, check the logs for:

```
✓ Should see: "Loading embeddings..." for each collection
✗ Should NOT see: "Loading embedding model: BAAI/bge-small-en-v1.5"
```

If using Vertex AI correctly, you'll see minimal local model loading.

## 🔄 Rollback Instructions

If something goes wrong:

```powershell
# 1. Stop the server

# 2. Restore backup
Remove-Item -Recurse -Force ./chroma_db
Copy-Item -Recurse ./chroma_db_backups/backup_TIMESTAMP ./chroma_db

# 3. Disable Vertex in config.py
# Set: USE_VERTEX_EMBEDDINGS = False

# 4. Restart server
npm start
```

## 💰 Cost Monitoring

- **Google Cloud Console** → Vertex AI → Dashboard → Usage
- Expected: **~$1-3/month** for 100 users
- Monitor first week closely to confirm costs

## ⚙️ Configuration Check

Before running, verify `config.py` has:

```python
USE_VERTEX_EMBEDDINGS = True  # Must be True
```

## 🐛 Troubleshooting

### "Module not found: vertex_embeddings"
- Make sure `vertex_embeddings.py` exists in your project root
- Run: `pip install google-cloud-aiplatform`

### "Credentials not found"
- Ensure `credentials.json` exists and is valid
- Test with: `gcloud auth application-default print-access-token`

### "Dimension mismatch error"
- This is expected! Old data is 384-dim, new is 768-dim
- Solution: The reindex script clears everything to avoid this

### Collections not reindexing
- Check admin panel for indexing status
- Manually trigger by clicking each collection in the UI
- Or wait - they'll index on first query

## 📞 Need Help?

1. Check `VERTEX_AI_MIGRATION.md` for full documentation
2. Review server logs for specific errors
3. Test with single query first before full deployment

---

**⚡ Quick Answer**: Just run `python reindex_with_vertex.py` and type "yes"
