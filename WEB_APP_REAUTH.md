# 🌐 Enable Shared Drives in Your Web App

## The Problem
Your RAG system can't access Google Drive Shared Drives because the authentication doesn't have the right permissions.

## The Solution (5 minutes)

### Step 1: Delete Old Token
```powershell
Remove-Item token.pickle
```
This removes the old authentication that doesn't have shared drives access.

### Step 2: Start Your Web Application
```powershell
python start_chat_system.py
```
Or:
```powershell
python chat_api.py
```

### Step 3: Re-authenticate Through the Web Interface

1. **Open your browser** and go to: http://localhost:5000/admin/dashboard

2. **Click "Connect Google Drive"** or **"Re-authorize Google Drive"**

3. **Sign in with Google** when prompted

4. **Grant permissions** - You'll see a new permission request for:
   - "See, edit, create, and delete all of your Google Drive files"
   - This is needed to access shared drives

5. **Click "Allow"**

6. You'll be redirected back with: **"✅ Authorization Successful!"**

### Step 4: Verify Shared Drives Access

The web interface should now show your shared drives in the file selector.

---

## Alternative: Quick CLI Check

If you want to verify shared drives access from command line:

```powershell
# Delete old token
Remove-Item token.pickle

# Start web app
python chat_api.py

# In browser: http://localhost:5000/admin/gdrive/authorize
# Complete authentication
# Then check token works:

python -c "from auth import authenticate_google_drive; service = authenticate_google_drive(); drives = service.drives().list(pageSize=10).execute(); print('Shared drives:', [d['name'] for d in drives.get('drives', [])])"
```

---

## What Changed?

✅ **OAuth Scopes Updated** in:
- `google_drive_oauth.py` (web OAuth flow)
- `oauth_config.py` (main config)
- `auth.py` (CLI fallback)

✅ **Added Permission**:
- `https://www.googleapis.com/auth/drive` (full drive access for shared drives)

✅ **Existing Permissions** (kept):
- `drive.readonly` (read files)
- `drive.metadata.readonly` (list files)

---

## Next Steps After Authentication

Once you've re-authenticated through the web app:

### 1. Delete Old Database
```powershell
Remove-Item -Recurse -Force .\chroma_db\
```

### 2. Re-index from Shared Drive
```powershell
python folder_indexer.py
```
- Select your shared drive (e.g., "7MM Resources")
- Select the folder (e.g., "Admin/Traffic")
- Choose "Full Re-indexing"

### 3. Verify CSV Fix
```powershell
python verify_csv_autofetch.py
```
Should show: **"✅ ALL TESTS PASSED!"**

### 4. Test in Chat
Query: "What is the January 2025 sales total for Altoona market?"

Expected: **$450,866.30** (all 414 rows)

---

## Troubleshooting

### "Still can't see shared drives"
- Make sure you deleted `token.pickle` before re-authenticating
- Check that you clicked "Allow" on all permissions
- Restart the web application after authentication

### "redirect_uri_mismatch error"
Your `credentials.json` already has the correct redirect URI:
```
http://localhost:5000/admin/gdrive/callback
```
This should work perfectly with the web app.

### "Files not showing up after re-indexing"
Run the folder indexer again and carefully select:
1. The shared drive (not "My Drive")
2. The correct folder within that shared drive

---

**Time Required:** 5 minutes  
**Status:** ✅ Code ready, just need to re-authenticate  
**Result:** Access to shared drives + 100% CSV data
