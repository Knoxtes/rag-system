# RAG System - Plesk Obsidian 18.0.73 on AlmaLinux 9.7
## Deployment Guide for Ask.7MountainsMedia.com

This guide provides step-by-step instructions for deploying the RAG Chat System to Plesk Obsidian 18.0.73 running on AlmaLinux 9.7.

---

## 📋 Prerequisites

### System Requirements
- **Plesk Version**: Obsidian 18.0.73 Update #4 or higher
- **OS**: AlmaLinux 9.7 (Moss Jungle Cat)
- **Node.js**: 18.x, 20.x, or 22.x (managed by Plesk at `/opt/plesk/node/`)
- **Python**: 3.8+ (typically 3.9 or higher on AlmaLinux 9.7)
- **Memory**: Minimum 4GB RAM (8GB recommended for large document collections)
- **Storage**: ~2GB for application + variable space for document database

### Required Files (Not in Repository)
These files contain sensitive credentials and must be uploaded separately:
- `credentials.json` - Google Cloud service account credentials
- `token.pickle` - Google OAuth token (generated after first auth)
- `.env` - Environment configuration (see template below)
- `chroma_db/` - Vector database folder (if migrating existing data)

---

## 🚀 Quick Start Deployment

### Method 1: Automated Setup (Recommended)

1. **Clone Repository via SSH**
   ```bash
   ssh user@your-server.com
   cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
   git clone https://github.com/Knoxtes/rag-system.git .
   ```

2. **Run Setup Script**
   ```bash
   chmod +x setup-plesk.sh
   ./setup-plesk.sh
   ```

3. **Upload Required Files**
   - Use Plesk File Manager or SFTP
   - Upload `credentials.json`, `token.pickle`, and `.env` to application root
   - Upload `chroma_db/` folder if migrating data

4. **Configure Plesk Node.js App**
   - Go to: Domains → Ask.7MountainsMedia.com → Node.js
   - Enable Node.js
   - Apply settings from Section 4 below

5. **Restart Application**
   - Click "Restart" in Plesk Node.js interface

---

## 📦 Method 2: Manual Installation

### Step 1: Access Server via SSH

```bash
ssh user@your-server.com
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
```

### Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/Knoxtes/rag-system.git .

# Or pull latest changes if already cloned
git pull origin main
```

### Step 3: Install Python Dependencies

```bash
# Use requirements-linux.txt for clean Linux-compatible dependencies
python3 -m pip install --user -r requirements-linux.txt

# Or use production requirements (more comprehensive)
python3 -m pip install --user -r requirements-production.txt
```

### Step 4: Install Node.js Dependencies

Plesk manages Node.js installations at `/opt/plesk/node/{version}/`. Use the appropriate version:

```bash
# Detect and use Plesk's Node.js (22.x recommended)
NPM_CMD="/opt/plesk/node/22/bin/npm"

# Install root dependencies
$NPM_CMD install

# Install React app dependencies
cd chat-app
$NPM_CMD install
```

### Step 5: Build React Frontend

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app

# Build production version
/opt/plesk/node/22/bin/npm run build
```

**Expected output**: `chat-app/build/` directory with compiled React app

**Note**: If you encounter localStorage errors with Node.js 25.x, use Node.js 22.x or 20.x instead.

### Step 6: Create Required Directories

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com

# Create logs directory
mkdir -p logs
chmod 755 logs

# Create temp directory for uploads
mkdir -p tmp
chmod 755 tmp
```

---

## 🔧 Step 3: Environment Configuration

Create `.env` file in the application root:

```bash
# ===========================================
# RAG SYSTEM - PRODUCTION CONFIGURATION
# Domain: Ask.7MountainsMedia.com
# ===========================================

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_SECRET_KEY=<generate-with-python-secrets>
JWT_SECRET_KEY=<generate-with-python-secrets>

# Server Ports
PORT=3000
FLASK_PORT=5001

# Domain Configuration
DOMAIN=Ask.7MountainsMedia.com
CORS_ORIGINS=https://Ask.7MountainsMedia.com
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback

# Google Cloud Configuration
GOOGLE_API_KEY=<your-google-api-key>
PROJECT_ID=<your-gcp-project-id>
LOCATION=us-central1

# Database Configuration
CHROMA_DB_PATH=./chroma_db
VECTOR_DIMENSION=384

# Performance Tuning
MAX_WORKERS=4
CACHE_EXPIRY=21600
ENABLE_REDIS_CACHE=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/rag-system.log
```

### Generate Secret Keys

```bash
# Generate Flask secret key
python3 -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"

# Generate JWT secret key
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

---

## 🎛️ Step 4: Plesk Node.js Configuration

### Navigate to Node.js Settings
1. Login to Plesk
2. Go to: **Domains** → **Ask.7MountainsMedia.com** → **Node.js**
3. Click **"Enable Node.js"**

### Application Settings

| Setting | Value |
|---------|-------|
| **Node.js Version** | 22.x (recommended) or 20.x |
| **Application Mode** | production |
| **Application Root** | `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com` |
| **Document Root** | `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app/build` |
| **Application Startup File** | `server.js` |

### Environment Variables

Add these in Plesk Node.js interface (click "Add variable" for each):

```
FLASK_ENV=production
DEBUG=False
NODE_ENV=production
PORT=3000
FLASK_PORT=5001
DOMAIN=Ask.7MountainsMedia.com
CORS_ORIGINS=https://Ask.7MountainsMedia.com
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback
```

**Note**: Sensitive keys (FLASK_SECRET_KEY, JWT_SECRET_KEY, GOOGLE_API_KEY) should be loaded from `.env` file for security.

---

## ✅ Step 5: Verification & Testing

### 1. Restart the Application

In Plesk Node.js settings, click **"Restart App"**

### 2. Health Check

Visit: `https://Ask.7MountainsMedia.com/api/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "rag-system-unified",
  "timestamp": "2025-11-21T19:28:21.686Z",
  "node_server": "running",
  "flask_backend": "running",
  "rag_initialized": true,
  "backend_url": "http://127.0.0.1:5001"
}
```

### 3. Frontend Access

Visit: `https://Ask.7MountainsMedia.com`

You should see the RAG Chat interface with:
- Dark theme UI
- Login button (Google OAuth)
- Collection selector
- Chat input field

### 4. Test Authentication

1. Click "Login with Google"
2. Complete OAuth flow
3. Should redirect back to `https://Ask.7MountainsMedia.com/auth/callback`
4. Should load chat interface with authenticated session

### 5. Test Chat Functionality

1. Select a document collection
2. Type a test query
3. Verify response with source citations
4. Check response time (should be <5 seconds for first query)

---

## 🔍 Troubleshooting

### Issue: 502 Bad Gateway

**Causes:**
- Flask backend not starting
- Python dependencies missing
- Credentials files missing

**Solutions:**
```bash
# Check if Flask is running
ps aux | grep python | grep chat_api

# Check Python dependencies
python3 -m pip list | grep -i flask

# Verify credentials
ls -la credentials.json token.pickle

# Check logs
tail -f logs/*.log
```

### Issue: React Build Not Found

**Error:** "React build not found. Run 'npm run build' first."

**Solution:**
```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app
/opt/plesk/node/22/bin/npm run build

# Verify build exists
ls -la build/
```

### Issue: localStorage Error (Node.js 25.x)

**Error:** "Failed to compile Security error cannot initialize local storage"

**Solution:** Switch to Node.js 22.x or 20.x in Plesk Node.js settings. Node.js 25.x has a known localStorage bug.

### Issue: OAuth Redirect Fails

**Error:** Redirect URI mismatch

**Solution:**
1. Go to Google Cloud Console
2. Navigate to: APIs & Services → Credentials
3. Edit OAuth 2.0 Client ID
4. Add authorized redirect URI: `https://Ask.7MountainsMedia.com/auth/callback`
5. Save and wait 5 minutes for propagation

### Issue: Port Conflicts

**Error:** "Port 3000 already in use"

**Solution:**
```bash
# Check what's using the port
lsof -i :3000

# Kill the process if needed
kill -9 <PID>

# Or change PORT in .env and Plesk environment variables
```

### Issue: Python Module Not Found

**Error:** "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
# Reinstall Python dependencies
python3 -m pip install --user -r requirements-linux.txt

# Verify installation
python3 -m pip show flask
```

---

## 📊 Performance Optimization

### For Large Document Collections (>1000 docs)

1. **Enable Redis Caching**
   ```bash
   # Install Redis
   sudo yum install redis
   sudo systemctl enable redis
   sudo systemctl start redis
   
   # Update .env
   ENABLE_REDIS_CACHE=true
   ```

2. **Increase Worker Processes**
   ```
   # In .env
   MAX_WORKERS=8
   ```

3. **Optimize ChromaDB**
   ```bash
   # Compact vector database
   cd chroma_db
   # Run maintenance scripts if needed
   ```

### Resource Monitoring

```bash
# Check memory usage
free -h

# Check disk space
df -h

# Monitor application
htop

# View logs in real-time
tail -f logs/rag-system.log
```

---

## 🔄 Updating the Application

### Pull Latest Changes

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
git pull origin main
```

### If Backend Changed

```bash
# Update Python dependencies
python3 -m pip install --user -r requirements-linux.txt

# Restart in Plesk
```

### If Frontend Changed

```bash
# Rebuild React app
cd chat-app
/opt/plesk/node/22/bin/npm install
/opt/plesk/node/22/bin/npm run build

# Restart in Plesk
```

---

## 🛡️ Security Best Practices

1. **Never commit sensitive files**
   - Keep `.env`, `credentials.json`, `token.pickle` out of Git
   - Already configured in `.gitignore`

2. **Use strong secret keys**
   - Generate with `secrets.token_hex(32)`
   - Rotate periodically

3. **Limit API access**
   - Configure Google Cloud Console to restrict API keys to specific domains
   - Enable OAuth consent screen

4. **Monitor logs**
   - Regularly check `logs/*.log` for suspicious activity
   - Set up log rotation

5. **Keep dependencies updated**
   ```bash
   python3 -m pip list --outdated
   npm outdated
   ```

---

## 📞 Support & Resources

### Documentation
- Main README: `/README.md`
- Production Checklist: `/PRODUCTION_CHECKLIST.md`
- Google Drive Setup: `/DOCUMENTAI_SETUP.md`

### Logs Location
- Application logs: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/logs/`
- Plesk logs: Domains → Ask.7MountainsMedia.com → Logs

### Quick Commands

```bash
# View application logs
tail -f logs/rag-system.log

# Check service status
systemctl status plesk-web-socket

# Restart Plesk services
systemctl restart plesk-web-socket

# Test Python backend directly
python3 chat_api.py --port 5001
```

---

## ✨ Features Enabled

- ✅ RAG-powered chat with document retrieval
- ✅ Google Drive integration
- ✅ Multi-collection support
- ✅ OAuth authentication
- ✅ Secure JWT tokens
- ✅ Vector search with ChromaDB
- ✅ OCR for scanned documents
- ✅ Semantic caching
- ✅ Production-grade error handling
- ✅ Comprehensive logging

---

**Deployment Target:** Ask.7MountainsMedia.com  
**Status:** Production Ready ✅  
**Last Updated:** November 2025
