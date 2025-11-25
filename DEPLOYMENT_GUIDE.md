# RAG System - Production Deployment Guide

## Quick Start (2 Steps)

### Step 1: Pull Latest Code via Plesk GUI ✅
1. Open Plesk Control Panel
2. Navigate to ask.7mountainsmedia.com
3. Go to **Git** section
4. Click **Pull**
5. Wait for it to complete (should be instant now - no more permission errors)

### Step 2: Deploy via SSH
```bash
cd /var/www/vhosts/7mountainsmedia.com/ask.7mountainsmedia.com
chmod +x deploy-production.sh
./deploy-production.sh
```

That's it! The script handles everything:
- Cleans up old files
- Installs dependencies
- Builds React frontend
- Starts Node.js and Flask
- Verifies everything is working

---

## What Gets Deployed

**Frontend (React 19)**
- Built to `chat-app/build`
- Served by Node.js on port 3000
- Uses relative API paths (works from any domain)

**Backend (Flask + Express)**
- Express proxy on port 3000 → routes API calls to Flask
- Flask on port 5001 → handles business logic
- Google Drive integration included

**Architecture:**
```
Browser (https://ask.7mountainsmedia.com)
    ↓
Express on 3000 (serves React + proxies /api, /auth, /chat)
    ↓
Flask on 5001 (chat logic, OAuth, Google Drive)
```

---

## Available Scripts

### Full Deployment
```bash
./deploy-production.sh
```
Does everything: clean, install, build, start, verify

### Frontend Rebuild Only
```bash
./rebuild-frontend-production.sh
```
Rebuild React without full deployment (if you only changed frontend code)

### Node.js Module Fix
```bash
./fix-node-modules.sh
```
Complete npm rebuild from scratch (only if npm is broken)

---

## Verification

### 1. Check Health Endpoint
```bash
curl http://ask.7mountainsmedia.com/api/health
```
Should return: `{"status":"healthy",...}`

### 2. Check Frontend
```bash
curl http://ask.7mountainsmedia.com
```
Should return HTML starting with `<!doctype html>`

### 3. Test in Browser
Visit: https://ask.7mountainsmedia.com

Should see:
- Login page (no console errors)
- "Sign in with Google" button
- Chat interface after login

---

## Troubleshooting

### Plesk Git Pull Still Fails
- Check if node_modules exists: `ls -la node_modules`
- If it does, Plesk can remove it before pull
- `.gitignore` now prevents it from being committed

### Deployment Script Fails
```bash
# Check Node.js is running
ps aux | grep "node server"

# Check logs
tail -f nohup.out

# Check port 3000 is available
lsof -i :3000

# Kill any existing process
pkill -f "node server"
```

### Frontend Shows Errors
1. Check `.env` exists and has correct values
2. Check REACT_APP_API_BASE_URL is empty (uses relative paths)
3. Check browser console for actual errors
4. Rebuild frontend: `./rebuild-frontend-production.sh`

### Flask Not Responding
```bash
# Check Flask process
ps aux | grep "python.*chat_api"

# Check port 5001
lsof -i :5001

# Logs should be visible in nohup.out
tail -30 nohup.out | grep -i flask
```

---

## Environment Variables

Critical `.env` settings:
```
REACT_APP_API_BASE_URL=''  # Empty = uses current domain
OAUTH_REDIRECT_URI=https://ask.7mountainsmedia.com/auth/callback
FLASK_ENV=production
DEBUG=False
```

Most other variables have good defaults. See `.env` comments for details.

---

## Post-Deployment Checklist

- [ ] Plesk Git Pull succeeded without errors
- [ ] `./deploy-production.sh` completed successfully  
- [ ] Health check returns healthy status
- [ ] Frontend loads at https://ask.7mountainsmedia.com
- [ ] OAuth login button visible (no 403 errors)
- [ ] Can log in with Google account
- [ ] Chat interface works
- [ ] No console errors in browser
- [ ] Flask backend responsive on port 5001

---

## Need Help?

Check these files:
- `PLESK_GIT_PULL_FIX.md` - Git integration details
- `nohup.out` - Server logs
- `.env` - Configuration
- `server.js` - Express proxy config
- `chat_api.py` - Flask app

All recent commits are on `origin/main` and ready to deploy!
