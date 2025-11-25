# RAG System - Plesk Git Pull Solution

## Issue
Plesk Git Pull GUI was failing with permission errors on `node_modules` files.

## Root Cause
`node_modules` directory was accidentally committed to git, causing permission conflicts when Plesk tried to update files from different systems (Linux → Windows).

## Solution Applied ✅
Removed `node_modules` from git tracking completely. The `.gitignore` already had it excluded, but the files needed to be removed from git history.

**Commits:**
- `09f06a1` - Remove node_modules from git tracking

## Now Plesk Can Pull Cleanly

You can now use the **Plesk Git Pull GUI** without errors.

### Steps:

1. **Open Plesk Control Panel**
   - Navigate to your domain (ask.7mountainsmedia.com)
   - Go to "Git" section

2. **Click "Pull"**
   - Should now pull successfully without permission errors
   - This will pull all recent commits including:
     - Frontend API configuration fixes
     - Deployment scripts
     - Node_modules cleanup

3. **After Successful Pull**

   SSH into your server and run the deployment script:
   ```bash
   cd /var/www/vhosts/7mountainsmedia.com/ask.7mountainsmedia.com
   chmod +x deploy-production.sh
   ./deploy-production.sh
   ```

   This script will:
   - Install all npm dependencies fresh
   - Build the React frontend
   - Start Node.js and Flask servers
   - Verify everything is working

4. **Verify Deployment**
   ```bash
   curl http://localhost:3000/api/health
   ```

## File Changes Summary

All necessary code is now committed:
- ✅ `chat-app/src/Auth.tsx` - Fixed API config to use relative paths
- ✅ `chat-app/src/App.tsx` - Fixed API config to use relative paths  
- ✅ `deploy-production.sh` - Complete deployment script
- ✅ `fix-node-modules.sh` - Node.js module rebuild script
- ✅ `rebuild-frontend-production.sh` - Frontend rebuild script

## What This Fixes

**Before:**
- Frontend hardcoded to `http://localhost:5001` 
- Browser couldn't connect from production domain
- Git pull failed with permission errors

**After:**
- Frontend uses **relative paths** (`/api`, `/auth`, `/chat`)
- Works from **any domain** (development, staging, production)
- Routes through **Node.js proxy** on port 3000 to Flask on port 5001
- **Git pull works cleanly** without permission errors

## System Architecture

```
Browser (https://ask.7mountainsmedia.com)
    ↓
Node.js/Express (port 3000) - Serves React + Proxies API
    ↓ /api/*, /auth/*, /chat/*
Flask Backend (port 5001) - Handles business logic
    ↓
Google Drive API
```

## Testing After Deployment

1. **Health Check:**
   ```bash
   curl http://localhost:3000/api/health
   ```

2. **Frontend Access:**
   - Visit https://ask.7mountainsmedia.com
   - Should see login page without console errors

3. **OAuth Flow:**
   - Click login
   - Should redirect to Google OAuth
   - After auth, should redirect back and show chat interface

## Support

If Plesk Git Pull still fails:
1. Check file permissions: `ls -la node_modules 2>/dev/null | head` (should be empty)
2. Check git status: `cd /var/www/... && git status`
3. Run deploy-production.sh manually - it handles all cleanup automatically

---

**Last Updated:** November 25, 2025
**Deployment Status:** ✅ Ready for Plesk Git Pull
