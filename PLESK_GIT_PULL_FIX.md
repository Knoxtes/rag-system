# RAG System - Plesk Git Pull Solution

## Issue Fixed ✅
Plesk Git Pull GUI was failing with permission errors on `node_modules` files.

## Root Cause
`node_modules` directory was accidentally committed to git, causing permission conflicts when Plesk tried to update files from different systems.

## Solution Applied ✅
1. **Removed node_modules from git** - No more permission conflicts during git pull
2. **Removed git operations from deployment scripts** - Plesk handles git via GUI, scripts only build/deploy

**Commits:**
- `09f06a1` - Remove node_modules from git tracking
- `ee4fbc6` - Remove git operations from scripts (deploy-production.sh, rebuild-frontend-production.sh)

## Now Plesk Can Pull Cleanly

You can now use the **Plesk Git Pull GUI** without errors.

### Workflow:

1. **Step 1: Plesk Git Pull (GUI)**
   - Open Plesk Control Panel
   - Navigate to your domain (ask.7mountainsmedia.com)
   - Go to "Git" section
   - Click **"Pull"** ← Plesk handles this
   - Should complete without permission errors ✅

2. **Step 2: Deploy with SSH**

   After Plesk pull succeeds, SSH into your server:
   ```bash
   cd /var/www/vhosts/7mountainsmedia.com/ask.7mountainsmedia.com
   chmod +x deploy-production.sh
   ./deploy-production.sh
   ```

   This script will:
   - Clean up node_modules and lock files
   - Install npm dependencies fresh
   - Build React frontend
   - Start Node.js server (port 3000)
   - Verify health endpoint

3. **Step 3: Verify It Works**
   ```bash
   curl http://ask.7mountainsmedia.com/api/health
   ```

   Then visit: https://ask.7mountainsmedia.com

## File Changes Summary

All code is committed and ready:
- ✅ `chat-app/src/Auth.tsx` - Uses relative paths for API calls
- ✅ `chat-app/src/App.tsx` - Uses relative paths for API calls  
- ✅ `deploy-production.sh` - Deployment script (NO git operations)
- ✅ `rebuild-frontend-production.sh` - Frontend rebuild (NO git operations)
- ✅ `fix-node-modules.sh` - Node.js rebuild script

## Important: Deployment Scripts Don't Touch Git

**The deployment scripts no longer have any git operations:**
- ❌ No `git pull`
- ❌ No `git fetch`  
- ❌ No `git reset`

**Plesk handles git via GUI.** The scripts only:
- ✅ Clean up node_modules and lock files
- ✅ Install dependencies
- ✅ Build React
- ✅ Start services
- ✅ Verify health

## What This Fixes

**Before:**
- Frontend hardcoded to `http://localhost:5001` 
- Browser couldn't connect from production domain
- Git pull failed with permission errors
- Deployment scripts tried to pull git themselves

**After:**
- Frontend uses **relative paths** (`/api`, `/auth`, `/chat`)
- Works from **any domain** automatically
- **Git pull works cleanly** via Plesk GUI
- **Scripts only deploy**, no git operations
- Routes through **Node.js proxy** on port 3000 to Flask on port 5001

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
   curl http://ask.7mountainsmedia.com/api/health
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
