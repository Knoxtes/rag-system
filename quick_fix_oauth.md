# Quick OAuth Fix - 2 Steps

## The Problem
Your credentials.json has redirect URI: `http://localhost:5000/admin/gdrive/callback`  
But the auth code needs: `http://localhost:5000/`

## The Fix

### Step 1: Update Google Cloud Console (2 minutes)

1. Go to: https://console.cloud.google.com/apis/credentials?project=rag-chat-system

2. Click on your OAuth 2.0 Client ID (starts with `632169698669`)

3. Under "Authorized redirect URIs", click **+ ADD URI**

4. Add exactly this (copy/paste):
   ```
   http://localhost:5000/
   ```

5. Click **SAVE**

6. Wait 60 seconds

### Step 2: Run the script
```powershell
python simple_reauth.py
```

Done! ✅

---

## Alternative: If you can't access Google Cloud Console

Download new Desktop App credentials:

1. Go to: https://console.cloud.google.com/apis/credentials?project=rag-chat-system
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: RAG Desktop
5. Click **CREATE**
6. Click **DOWNLOAD JSON**
7. Replace your `credentials.json` with the downloaded file
8. Run `python simple_reauth.py`
