# 🔧 Fix Google OAuth Redirect URI Error

## The Problem
Your `credentials.json` has this redirect URI:
```
http://localhost:5000/admin/gdrive/callback
```

But the authentication flow needs:
```
http://localhost:5000/
```

## The Solution (2 minutes)

### Step 1: Open Google Cloud Console
1. Go to: https://console.cloud.google.com/apis/credentials
2. Sign in with your Google account
3. Select project: **rag-chat-system**

### Step 2: Add the Correct Redirect URI
1. Find your OAuth 2.0 Client ID (starts with `632169698669-...`)
2. Click the **pencil icon** (Edit) next to it
3. Scroll down to **"Authorized redirect URIs"**
4. Click **"+ ADD URI"**
5. Add this **exact** URI:
   ```
   http://localhost:5000/
   ```
6. Keep the existing URI (`http://localhost:5000/admin/gdrive/callback`)
7. Click **"SAVE"** at the bottom

### Step 3: Wait 1 Minute
Google takes ~30-60 seconds to propagate the changes.

### Step 4: Try Again
```powershell
python simple_reauth.py
```

---

## Alternative: Quick Fix Without Google Console

If you can't access Google Cloud Console, I can create a different credentials file for you:

### Option A: Create New OAuth Credentials
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: **"RAG System Desktop"**
5. Click **"CREATE"**
6. Download JSON file
7. Replace `credentials.json` with the downloaded file
8. Run `python simple_reauth.py`

### Option B: Use Web Application Flow (Not Recommended)
I can modify the code to use a different authentication method, but this is more complex.

---

## Quick Reference

### Your Current Credentials
- **Client ID:** `632169698669-n5sttmpaes91rj6v8qe17dcqlmr0fggr.apps.googleusercontent.com`
- **Project:** `rag-chat-system`
- **Current Redirect URI:** `http://localhost:5000/admin/gdrive/callback`
- **Needed Redirect URI:** `http://localhost:5000/`

### Why This Happened
The credentials were originally created for a web application (`/admin/gdrive/callback` route), but we're now using it for desktop authentication (simple `/` route).

### Google Cloud Console Direct Link
https://console.cloud.google.com/apis/credentials?project=rag-chat-system

---

## Troubleshooting

### "I don't have access to Google Cloud Console"
**Solution:** Ask the person who created the credentials to add the redirect URI, or create new OAuth credentials yourself.

### "The project doesn't exist"
**Solution:** You might be signed in with the wrong Google account. Make sure you're using the account that owns the `rag-chat-system` project.

### "Still getting redirect_uri_mismatch"
**Possible causes:**
1. Didn't wait 60 seconds after saving
2. Typed the URI wrong (must be exact: `http://localhost:5000/`)
3. Didn't click "SAVE" in Google Console
4. Browser cached the old configuration (try incognito mode)

---

**Time to fix:** 2-3 minutes  
**Difficulty:** Easy (just adding one URI)  
**Next step after fixing:** Run `python simple_reauth.py`
