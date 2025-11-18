# 🔑 Google Drive Shared Drives Access - Quick Fix

## Problem
The folder indexer can't see your shared drives because the current authentication token doesn't have the right permissions.

## Solution (2 minutes)

### Option A: Using the Menu (Easiest)
```powershell
python csv_fix_menu.py
# Select Option 3: Re-authenticate Google Drive
```

### Option B: Manual Steps
```powershell
# 1. Run the re-authentication script
python reauth_shared_drives.py

# 2. Follow the prompts:
#    - Confirm deletion of old token
#    - Browser will open for authorization
#    - Sign in with your Google account
#    - Grant permissions
#    - Copy the authorization code
#    - Paste it back in the terminal

# 3. Verify shared drives are now visible
```

## What Changed

### Before (Limited Access)
```python
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]
```
❌ Can only see personal "My Drive" files

### After (Full Access)
```python
SCOPES = [
    'https://www.googleapis.com/auth/drive',  # Full access
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]
```
✅ Can see personal files AND shared drives

## After Re-authenticating

You should see your shared drives when running:
```powershell
python folder_indexer.py
```

Expected output:
```
📁 Fetching Shared Drives...
✓ Found X Shared Drives

SELECT SHARED DRIVES TO BROWSE
================================
Which Shared Drives do you want to browse folders from?

1. 7MM Resources
2. [Other shared drives...]
```

## Then Complete the CSV Fix

Once you can see shared drives:

1. **Delete the database**:
   ```powershell
   Remove-Item -Recurse -Force .\chroma_db\
   ```

2. **Re-index with Admin/Traffic collection**:
   ```powershell
   python folder_indexer.py
   # Select the shared drive with your data
   # Select "Admin/Traffic" collection
   # Choose "Full Re-indexing"
   ```

3. **Verify the fix**:
   ```powershell
   python verify_csv_autofetch.py
   ```

4. **Test the chat system**:
   ```powershell
   python start_chat_system.py
   # Query: "What is January 2025 Altoona sales total?"
   # Expected: $450,866.30
   ```

## Troubleshooting

### "No shared drives found"
**Possible causes:**
- Wrong Google account (use the account that has shared drive access)
- Not a member of any shared drives (ask admin to add you)
- Permissions not fully granted during authorization

**Solution:**
```powershell
# Delete token and try again
Remove-Item token.pickle
python reauth_shared_drives.py
```

### "Authorization failed"
**Check:**
- `credentials.json` exists in the folder
- Using the correct OAuth credentials type ("Desktop app" or "Installed app")
- Browser isn't blocking the authorization popup

### "Error: redirect_uri mismatch"
**Solution:**
The auth script uses OOB (out-of-band) flow which works with console apps.
If you see this error, make sure your `credentials.json` is configured for "Desktop app" type.

## Security Note

The `https://www.googleapis.com/auth/drive` scope grants full read/write access to Google Drive. This application only reads files and doesn't modify them. The code is open source and you can verify what it does.

If you prefer more restrictive permissions, you would need to:
1. Limit indexing to specific folders (not shared drives)
2. Use a different authentication approach
3. Manually download CSVs and index from local files

---

**Status**: ✅ Fix implemented  
**Files Changed**: `auth.py`, `reauth_shared_drives.py`, `csv_fix_menu.py`  
**Next Step**: Run `python reauth_shared_drives.py`
