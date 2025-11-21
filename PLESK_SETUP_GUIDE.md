# RAG System - Plesk Deployment Guide
## Optimized for Ask.7MountainsMedia.com

**Target Environment:**
- **Domain:** Ask.7MountainsMedia.com
- **Server:** Plesk Obsidian 18.0.73 Update #4 Web Host Edition
- **OS:** AlmaLinux 9.7 (Moss Jungle Cat)
- **Node.js:** 25.2.0
- **Python:** 3.8+

---

## 🚀 Quick Start

### Prerequisites
- SSH access to your Plesk server
- Git installed on the server
- Python 3.8+ and pip
- Node.js 25.2.0 (managed by Plesk)

### One-Command Deployment

```bash
# Clone repository
git clone https://github.com/Knoxtes/rag-system.git
cd rag-system

# Run deployment script
./deploy.sh

# Start the application
npm start
```

---

## 📋 Detailed Setup Instructions

### Step 1: Enable Node.js in Plesk

1. Log into Plesk Control Panel
2. Navigate to **Domains** → **Ask.7MountainsMedia.com**
3. Click **Node.js** in the sidebar
4. **Enable Node.js** for the domain
5. Configure settings:
   - **Node.js Version:** 25.2.0
   - **Application Mode:** production
   - **Application Root:** `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com`
   - **Document Root:** `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app/build`
   - **Application Startup File:** `server.js`
6. Click **Apply**

### Step 2: Clone Repository

SSH into your server:
```bash
ssh user@7mountainsmedia.com
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
```

Clone the repository:
```bash
git clone https://github.com/Knoxtes/rag-system.git .
```

### Step 3: Install Dependencies

#### Python Dependencies
```bash
python3 -m pip install --user -r requirements-production.txt
```

#### Node.js Dependencies
```bash
# Use Plesk's Node.js installation
/opt/plesk/node/25/bin/npm install
```

### Step 4: Build React Frontend

```bash
cd chat-app
/opt/plesk/node/25/bin/npm install
/opt/plesk/node/25/bin/npm run build
cd ..
```

Verify the build:
```bash
ls -la chat-app/build/
```

### Step 5: Configure Environment Variables

Create a `.env` file in the application root:

```bash
# Production URLs
FLASK_ENV=production
NODE_ENV=production
DEBUG=False

# Server Ports
PORT=3000
FLASK_PORT=5001

# Domain Configuration
CORS_ORIGINS=https://Ask.7MountainsMedia.com
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback

# Generate Secret Keys (run these commands to generate)
# python3 -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET_KEY=your_generated_secret_key_here
JWT_SECRET_KEY=your_generated_jwt_secret_key_here

# Google Cloud Configuration
GOOGLE_API_KEY=your_google_api_key
PROJECT_ID=your_project_id
LOCATION=us-central1
```

**Also add these environment variables in Plesk:**
1. Go to **Domains** → **Ask.7MountainsMedia.com** → **Node.js**
2. Scroll to **Environment Variables**
3. Add each variable from above

### Step 6: Upload Required Files

Upload these files via SFTP or Plesk File Manager to `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/`:

**Required Files:**
- `credentials.json` - Google Cloud service account credentials
- `token.pickle` - Google OAuth token (if you have it)
- `.env` - Environment configuration (created in Step 5)

**Optional Large Files:**
- `chroma_db/` - Vector database (520 MB) - upload via SFTP for better performance

### Step 7: Create Logs Directory

```bash
mkdir -p /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/logs
chmod 755 logs
```

### Step 8: Update Google Cloud OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **APIs & Services** → **Credentials**
3. Edit your OAuth 2.0 Client ID
4. Add to **Authorized redirect URIs:**
   ```
   https://Ask.7MountainsMedia.com/auth/callback
   ```
5. Save changes

### Step 9: Restart Application in Plesk

1. Go to **Domains** → **Ask.7MountainsMedia.com** → **Node.js**
2. Click **Restart Application**
3. Wait 10-15 seconds for the application to start

### Step 10: Verify Deployment

**Health Check:**
Visit: `https://Ask.7MountainsMedia.com/api/health`

Expected response:
```json
{
  "status": "healthy",
  "service": "rag-system-unified",
  "timestamp": "2024-11-21T19:35:00Z",
  "node_server": "running",
  "flask_backend": "running",
  "rag_initialized": true
}
```

**Frontend:**
Visit: `https://Ask.7MountainsMedia.com`
- Should display the React chat interface

**Authentication:**
Click "Login with Google"
- Should redirect to Google OAuth
- After login, should redirect back successfully

---

## 🏗️ System Architecture

```
User Request
    ↓
Ask.7MountainsMedia.com (HTTPS)
    ↓
Node.js Server (Port 3000)
    ├─→ Serves React Build (Static Files)
    └─→ Proxies API Requests
            ↓
        Flask Backend (Port 5001)
            ├─→ RAG System (ChromaDB)
            ├─→ Google Drive Integration
            └─→ Gemini AI
```

---

## 🔧 Configuration Details

### Node.js Server (server.js)
- Serves React frontend
- Proxies API requests to Flask backend
- Handles health checks
- Auto-restarts Flask on failure

### Flask Backend (chat_api.py)
- RAG processing with ChromaDB
- Google Drive document access
- Authentication & JWT tokens
- Rate limiting
- Logging & monitoring

### React Frontend (chat-app/)
- Modern dark-themed UI
- Real-time chat interface
- Google Drive browser
- Markdown rendering

---

## 🐛 Troubleshooting

### Application Won't Start (502 Bad Gateway)

**Check Plesk Logs:**
```bash
tail -f /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/logs/nodejs_app_*
```

**Common Issues:**
1. **Missing build directory**
   ```bash
   cd chat-app && /opt/plesk/node/25/bin/npm run build
   ```

2. **Python dependencies not installed**
   ```bash
   python3 -m pip install --user -r requirements-production.txt
   ```

3. **Missing credentials.json**
   - Upload via SFTP or Plesk File Manager

4. **Wrong Node.js version**
   - Verify in Plesk: Should be 25.2.0

### Flask Backend Not Responding

**Check if Flask is running:**
```bash
ps aux | grep python | grep chat_api
```

**Check Flask logs:**
```bash
tail -f /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/logs/rag_system.log
```

**Restart Flask:**
```bash
# Plesk will auto-restart Flask when you restart the Node.js app
```

### OAuth Redirect Fails

**Verify redirect URI in Google Cloud Console:**
1. Must exactly match: `https://Ask.7MountainsMedia.com/auth/callback`
2. Check CORS_ORIGINS environment variable
3. Check OAUTH_REDIRECT_URI in .env and Plesk environment variables

### Build Fails with Node.js 25.x

**Solution 1: Use build wrapper (already included)**
The project includes a build wrapper that handles Node.js 25.x compatibility.

**Solution 2: Check for localStorage errors**
```bash
cd chat-app
rm -rf node_modules package-lock.json
/opt/plesk/node/25/bin/npm install
/opt/plesk/node/25/bin/npm run build
```

### Port Conflicts

**Check if ports are in use:**
```bash
netstat -tulpn | grep -E '3000|5001'
```

**Change ports in Plesk environment variables:**
- `PORT=3001` (for Node.js)
- `FLASK_PORT=5002` (for Flask)

---

## 🔄 Updating the Application

When you push changes to GitHub:

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
git pull origin main

# If frontend changed:
cd chat-app
/opt/plesk/node/25/bin/npm install
/opt/plesk/node/25/bin/npm run build
cd ..

# If backend changed:
python3 -m pip install --user -r requirements-production.txt

# Restart in Plesk:
# Domains → Ask.7MountainsMedia.com → Node.js → Restart Application
```

---

## 📊 Performance Optimization

### Caching
- **Vector Cache:** ChromaDB caches embeddings
- **API Cache:** Google Drive responses cached
- **Session Cache:** JWT tokens cached for 7 days

### Monitoring
- **Health Endpoint:** `/api/health`
- **Logs Directory:** `/logs/`
- **Plesk Monitoring:** Available in Plesk dashboard

### Database
- **Collections:** 11+ document collections
- **Documents:** 2,000+ indexed documents
- **Size:** ~520 MB vector database

---

## 🔐 Security Checklist

- [x] HTTPS enabled (Plesk SSL certificate)
- [x] JWT token authentication
- [x] Secure session cookies
- [x] CORS properly configured
- [x] Rate limiting enabled
- [x] Credentials in .env (not in code)
- [x] Google OAuth configured
- [x] Logs directory with proper permissions

---

## 📞 Support

**For Deployment Issues:**
1. Check this troubleshooting guide
2. Review Plesk logs
3. Verify all environment variables
4. Ensure credentials.json exists

**For Application Issues:**
1. Check `/logs/rag_system.log`
2. Test health endpoint
3. Verify Google Drive access
4. Check ChromaDB status

---

## 📋 Quick Reference

**Key Files:**
- `server.js` - Node.js proxy server
- `chat_api.py` - Flask backend
- `passenger_wsgi.py` - WSGI entry point (alternative)
- `requirements-production.txt` - Python dependencies
- `package.json` - Node.js configuration
- `.nvmrc` - Node.js version (25.2.0)

**Key Directories:**
- `chat-app/` - React frontend source
- `chat-app/build/` - Production React build
- `logs/` - Application logs
- `chroma_db/` - Vector database
- `utils/` - Development utility scripts

**Important URLs:**
- Frontend: `https://Ask.7MountainsMedia.com`
- Health Check: `https://Ask.7MountainsMedia.com/api/health`
- OAuth Callback: `https://Ask.7MountainsMedia.com/auth/callback`

---

**Status:** Production Ready ✅  
**Last Updated:** November 2024  
**Version:** 1.0.0  
**Domain:** Ask.7MountainsMedia.com
