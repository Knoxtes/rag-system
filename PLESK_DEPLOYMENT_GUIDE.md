# 🚀 RAG System - Plesk Deployment Guide
## Optimized for Ask.7MountainsMedia.com
### Plesk Obsidian 18.0.74 | AlmaLinux 9.7 | Node.js 22.21.1

---

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Server Setup](#initial-server-setup)
3. [Git-Based Deployment](#git-based-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Building the Application](#building-the-application)
6. [Plesk Node.js Configuration](#plesk-nodejs-configuration)
7. [Verification & Testing](#verification--testing)
8. [Troubleshooting](#troubleshooting)
9. [Updates & Maintenance](#updates--maintenance)

---
test

## Prerequisites

### Required Accounts & Credentials
- ✅ Google Cloud Project with enabled APIs:
  - Vertex AI API
  - Document AI API
  - Google Drive API
- ✅ Google OAuth 2.0 Client ID configured
- ✅ SSH access to Plesk server
- ✅ Git repository access (GitHub)

### System Requirements
- **OS**: AlmaLinux 9.7 (Moss Jungle Cat)
- **Control Panel**: Plesk Obsidian 18.0.74 (Web Host Edition)
- **Node.js**: 22.21.1 (managed by Plesk at `/opt/plesk/node/22/`)
- **Python**: 3.9+ (system Python)
- **Memory**: 2GB+ RAM recommended
- **Storage**: 1GB+ free space (excluding chroma_db)

---

## Initial Server Setup

### Step 1: Enable Node.js in Plesk

1. Log into **Plesk Control Panel**
2. Navigate to **Domains** → **Ask.7MountainsMedia.com**
3. Click **Node.js** in the left sidebar
4. Click **Enable Node.js**
5. Configure settings:
   - **Node.js version**: `22.21.1`
   - **Application mode**: `production`
   - **Application root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com`
   - **Document root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/chat-app/build`
   - **Application startup file**: `server.js`
6. Click **Apply** (don't start yet)

### Step 2: Connect via SSH

```bash
ssh your-username@7mountainsmedia.com
cd /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com
```

---

## Git-Based Deployment

### Step 3: Clone Repository

```bash
# If directory is empty
git clone https://github.com/Knoxtes/rag-system.git .

# If directory already exists
git init
git remote add origin https://github.com/Knoxtes/rag-system.git
git fetch
git checkout -f feature/easyocr-integration
```

### Step 4: Configure Git for Updates

```bash
# Create a deployment script
cat > deploy-update.sh << 'EOF'
#!/bin/bash
echo "🔄 Pulling latest changes..."
git fetch origin
git reset --hard origin/feature/easyocr-integration
echo "✅ Repository updated"
EOF

chmod +x deploy-update.sh
```

---

## Environment Configuration

### Step 5: Create Production .env File

```bash
# Copy example and edit
cp .env.example .env
nano .env
```

Update the following values in `.env`:

```bash
# ============================================
# RAG SYSTEM - PRODUCTION CONFIGURATION
# ============================================

# Google OAuth Configuration  
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Organization Access Control
ALLOWED_DOMAINS=7mountainsmedia.com

# OAuth Redirect URI - CRITICAL: Must match exactly!
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback

# Flask Security - Generate new keys!
# Run: python3 -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET_KEY=YOUR_GENERATED_SECRET_KEY_HERE
JWT_SECRET_KEY=YOUR_GENERATED_JWT_KEY_HERE

# Token Configuration
TOKEN_EXPIRY_HOURS=168
REFRESH_TOKEN_EXPIRY_DAYS=30

# Environment Settings
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# CORS Origins
CORS_ORIGINS=https://Ask.7MountainsMedia.com

# Google Cloud Settings (from your config.py)
GOOGLE_API_KEY=your-api-key
PROJECT_ID=rag-chatbot-475316
LOCATION=us-central1

# Performance Optimization
MAX_PARALLEL_WORKERS=5
USE_REDIS_CACHE=false

# Server Ports (Plesk managed)
PORT=3000
FLASK_PORT=5001
```

**Security Note**: Generate unique secret keys:
```bash
python3 -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

### Step 6: Upload Credentials

Upload these files via SFTP or Plesk File Manager:

1. **credentials.json** - Google Cloud Service Account
2. **token.pickle** - Google OAuth token (if you have it)
3. **chroma_db/** folder - Vector database (520MB via SFTP)

Place all files in: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/`

### Step 7: Update Google Cloud OAuth Settings

1. Go to https://console.cloud.google.com/apis/credentials
2. Select your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, add:
   ```
   https://Ask.7MountainsMedia.com/auth/callback
   ```
4. Save changes

---

## Building the Application

### Step 8: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install --upgrade pip
pip install -r requirements-production.txt

# Verify installation
python3 -c "import flask, chromadb, sentence_transformers; print('✅ All imports successful')"
```

### Step 9: Install Node.js Dependencies

Use Plesk's managed Node.js:

```bash
# Set Node.js path
export PATH="/opt/plesk/node/22/bin:$PATH"

# Verify version
node --version  # Should show v22.21.1
npm --version

# Install root dependencies
npm install

# Install React app dependencies
cd chat-app
npm install --legacy-peer-deps
cd ..
```

### Step 10: Build React Frontend

```bash
cd chat-app

# Use the Plesk build script
chmod +x install-and-build.sh
./install-and-build.sh

# Verify build completed
ls -lh build/
cd ..
```

Expected output:
```
✅ Build completed: /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/chat-app/build/
```

### Step 11: Create Logs Directory

```bash
mkdir -p logs
chmod 755 logs
```

---

## Plesk Node.js Configuration

### Step 12: Configure Environment Variables in Plesk

1. Go to **Plesk** → **Domains** → **Ask.7MountainsMedia.com** → **Node.js**
2. Click **Environment Variables**
3. Add these variables (click "+ Add Variable" for each):

| Variable Name | Value |
|---------------|-------|
| `FLASK_ENV` | `production` |
| `DEBUG` | `False` |
| `NODE_ENV` | `production` |
| `PORT` | `3000` |
| `FLASK_PORT` | `5001` |
| `FLASK_SECRET_KEY` | `<your-generated-key>` |
| `JWT_SECRET_KEY` | `<your-generated-key>` |
| `GOOGLE_API_KEY` | `<your-api-key>` |
| `PROJECT_ID` | `rag-chatbot-475316` |
| `LOCATION` | `us-central1` |
| `CORS_ORIGINS` | `https://Ask.7MountainsMedia.com` |
| `OAUTH_REDIRECT_URI` | `https://Ask.7MountainsMedia.com/auth/callback` |

4. Click **Apply**

### Step 13: Final Plesk Settings

Verify these settings in **Node.js** section:

- **Node.js Version**: `25.2.0` ✓
- **Application mode**: `production` ✓
- **Application Root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com` ✓
- **Document Root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/chat-app/build` ✓
- **Application Startup File**: `server.js` ✓
- **Environment Variables**: All set ✓

### Step 14: Start Application

1. In Plesk Node.js settings, click **Restart App**
2. Wait 10-15 seconds for both Node.js and Flask to start
3. Check application logs in Plesk if needed

---

## Verification & Testing

### Step 15: Health Check

Visit: https://Ask.7MountainsMedia.com/api/health

Expected response:
```json
{
  "status": "healthy",
  "service": "rag-system-unified",
  "timestamp": "2025-11-21T...",
  "node_server": "running",
  "flask_backend": "healthy",
  "rag_initialized": true,
  "backend_url": "http://127.0.0.1:5001"
}
```

### Step 16: Frontend Access

1. Visit: https://Ask.7MountainsMedia.com
2. You should see the chat interface
3. Click **"Login with Google"**
4. Complete OAuth flow
5. You should be redirected back and authenticated

### Step 17: Test Chat Functionality

1. Type a test query: "What is our vacation policy?"
2. First query: Should respond in 5-8 seconds
3. Same query again: Should respond in <50ms (cached)
4. Verify responses include source citations

### Step 18: Monitor Logs

```bash
# View application logs
tail -f logs/rag_system.log

# View Flask logs
tail -f logs/chat_api.log

# Check Plesk logs
# Go to Plesk → Domains → Ask.7MountainsMedia.com → Logs
```

---

## Troubleshooting

### Issue: Application won't start (502 Bad Gateway)

**Check 1**: Verify Node.js process
```bash
ps aux | grep node
```

**Check 2**: Verify Flask process
```bash
ps aux | grep python | grep chat_api
```

**Check 3**: Check application logs
```bash
tail -50 logs/rag_system.log
```

**Solution**: Restart in Plesk → Node.js → Restart App

---

### Issue: OAuth redirect fails

**Symptoms**: "redirect_uri_mismatch" error

**Solutions**:
1. Check `.env` file:
   ```bash
   grep OAUTH_REDIRECT_URI .env
   ```
   Must be: `https://Ask.7MountainsMedia.com/auth/callback`

2. Verify in Google Cloud Console:
   - APIs & Services → Credentials
   - OAuth 2.0 Client ID
   - Authorized redirect URIs must include the exact URL

3. No trailing slashes, must use HTTPS

---

### Issue: React build not found

**Symptoms**: 404 or "React build not found" message

**Solutions**:
```bash
cd chat-app
rm -rf build node_modules
npm install --legacy-peer-deps
./install-and-build.sh
cd ..
```

Verify: `ls -lh chat-app/build/index.html`

---

### Issue: Flask backend not responding

**Symptoms**: Chat requests timeout or fail

**Check logs**:
```bash
tail -f logs/rag_system.log
```

**Common causes**:
1. Python dependencies missing: `pip install -r requirements-production.txt`
2. Credentials missing: Check `credentials.json` exists
3. Port conflict: Check Flask port 5001 is available

**Restart**:
```bash
# In Plesk, restart the application
# Or manually:
pkill -f chat_api.py
# Plesk will auto-restart
```

---

### Issue: Module import errors

**Symptoms**: `ModuleNotFoundError` in logs

**Solution**:
```bash
# Activate virtual environment if using one
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements-production.txt

# Restart application in Plesk
```

---

### Issue: localStorage errors during build

**Symptoms**: Build fails with localStorage reference errors

**Solution**: This is handled by `build-wrapper.js`, but if it fails:
```bash
cd chat-app
npm install --save node-localstorage --legacy-peer-deps
npm run build:wrapper
cd ..
```

---

## Updates & Maintenance

### Updating the Application

When you push changes to GitHub:

```bash
# SSH into server
cd /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com

# Run deployment update script
./deploy-update.sh

# If frontend changed, rebuild
cd chat-app
./install-and-build.sh
cd ..

# If backend dependencies changed
pip install -r requirements-production.txt

# Restart application in Plesk
# Go to: Plesk → Domains → Ask.7MountainsMedia.com → Node.js → Restart App
```

### Automated Update Script

Create `auto-deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting automated deployment..."

# Pull latest changes
git fetch origin
git reset --hard origin/feature/easyocr-integration

# Update Python dependencies
echo "📦 Updating Python dependencies..."
pip install --upgrade -r requirements-production.txt

# Update Node dependencies and rebuild frontend
echo "⚛️ Rebuilding frontend..."
cd chat-app
./install-and-build.sh
cd ..

echo "✅ Deployment complete! Restart app in Plesk."
```

Make executable:
```bash
chmod +x auto-deploy.sh
```

### Backup Before Updates

```bash
# Backup .env and credentials
cp .env .env.backup
cp credentials.json credentials.json.backup
cp token.pickle token.pickle.backup 2>/dev/null || true

# Note: chroma_db should be backed up separately due to size
```

### Monitoring Performance

Check cache performance:
```bash
curl https://Ask.7MountainsMedia.com/api/stats
```

### Log Rotation

Logs are auto-rotated by Flask's RotatingFileHandler:
- Max size: 10MB per log
- Keeps 10 backup files
- Check: `ls -lh logs/`

---

## Performance Expectations

### Response Times
- **First-time query**: 5-8 seconds (RAG retrieval + LLM generation)
- **Cached query**: <50ms (99.9% faster)
- **Similar query (semantic cache)**: <200ms

### Resource Usage
- **Memory**: ~200-300MB typical
- **CPU**: <5% idle, 20-50% under load
- **Disk**: Minimal I/O (vectors pre-built)

### Optimizations Active
✅ Connection Pooling
✅ Parallel Search
✅ Redis Cache (if enabled)
✅ Semantic Cache
✅ Lazy Loading
✅ Response Compression
✅ SSE Streaming
✅ HNSW Optimization
✅ Fast Keyword Routing
✅ Query Result Caching
✅ Reduced Search Scope

---

## Security Checklist

- [x] Unique `FLASK_SECRET_KEY` generated
- [x] Unique `JWT_SECRET_KEY` generated
- [x] OAuth redirect URI matches exactly
- [x] CORS origins set to production domain only
- [x] `DEBUG=False` in production
- [x] Credentials files not in git (.gitignore)
- [x] HTTPS enabled for domain
- [x] Rate limiting configured
- [x] File permissions secure (644 for files, 755 for directories)

---

## Quick Reference

### Important Paths
```
Application Root:  /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com
React Build:       /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/chat-app/build
Logs:              /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/logs
Node.js:           /opt/plesk/node/22/bin/node
```

### Important URLs
```
Frontend:     https://Ask.7MountainsMedia.com
Health:       https://Ask.7MountainsMedia.com/api/health
OAuth:        https://Ask.7MountainsMedia.com/auth/login
Callback:     https://Ask.7MountainsMedia.com/auth/callback
```

### Important Commands
```bash
# Update from git
./deploy-update.sh

# Rebuild frontend
cd chat-app && ./install-and-build.sh

# View logs
tail -f logs/rag_system.log

# Check processes
ps aux | grep -E "node|python.*chat_api"

# Restart (in Plesk)
Domains → Ask.7MountainsMedia.com → Node.js → Restart App
```

---

## Support & Additional Resources

- **Repository**: https://github.com/Knoxtes/rag-system
- **Branch**: feature/easyocr-integration
- **Node.js Version**: 25.2.0
- **Python Version**: 3.9+

---

**🎉 Your RAG System is now deployed and optimized for Plesk Obsidian on AlmaLinux 9.7!**

Last Updated: November 21, 2025
