# Plesk Obsidian 18.0.74 Deployment Guide
## AlmaLinux 9.7 + Node.js Application

## Overview
Plesk Obsidian manages Node.js installations at `/opt/plesk/node/{version}/`. This guide uses Plesk's managed Node.js environment.

---

## Step 1: Enable Node.js in Plesk

1. Go to **Domains** → **chat.7mountainsmedia.com** (or Ask.7mountainsmedia.com)
2. Click **Node.js**
3. **Enable Node.js** for the domain
4. Select **Node.js version**: 22.x or 25.x (recommended: 22.x for stability)
5. Set **Application mode**: production
6. **Document Root**: Leave default for now (we'll set it after build)
7. **Application Startup File**: `server.js`
8. Click **Apply**

---

## Step 2: Clone Repository via SSH

SSH into your server:
```bash
ssh user@your-server.com
cd /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com
```

Clone the repository:
```bash
git clone https://github.com/Knoxtes/rag-system.git .
# Or if already cloned:
git pull origin feature/easyocr-integration
```

---

## Step 3: Install Python Dependencies

Still in SSH terminal:
```bash
python3 -m pip install --user -r requirements-production.txt
```

---

## Step 4: Install Root Node.js Dependencies

```bash
/opt/plesk/node/22/bin/npm install
# Or if using Node 25:
/opt/plesk/node/25/bin/npm install
```

---

## Step 5: Build React Application

```bash
cd chat-app
chmod +x install-and-build.sh
./install-and-build.sh
```

This script will:
- Auto-detect Plesk's Node.js installation
- Install all React dependencies with `--ignore-scripts` (avoids postinstall errors)
- Build the production React app

Expected output: `Build output: /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/chat-app/build/`

---

## Step 6: Upload Required Files

Via SFTP (FileZilla) or Plesk File Manager, upload to `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/`:

**Required files:**
- `credentials.json` (Google Cloud credentials)
- `token.pickle` (OAuth token)
- `.env` (updated with production URLs - see below)

**Large folder (520 MB - use SFTP):**
- `chroma_db/` (vector database)

---

## Step 7: Update .env for Production

Edit `.env` file and update these values:
```bash
# Production URLs
OAUTH_REDIRECT_URI=https://chat.7mountainsmedia.com/auth/callback
CORS_ORIGINS=https://chat.7mountainsmedia.com

# Generate new secret keys
FLASK_SECRET_KEY=[run: python -c "import secrets; print(secrets.token_hex(32))"]
JWT_SECRET_KEY=[run: python -c "import secrets; print(secrets.token_hex(32))"]

# Keep your existing Google Cloud values
GOOGLE_API_KEY=...
PROJECT_ID=...
LOCATION=...
```

---

## Step 8: Configure Plesk Node.js Application

Go back to Plesk → Domains → Node.js settings:

**Application Settings:**
- **Node.js Version**: 22.x (or 25.x if you used that)
- **Application Root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com`
- **Document Root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/chat-app/build`
- **Application Startup File**: `server.js`
- **Application Mode**: production

**Environment Variables** (click "Add variable" for each):
```
FLASK_ENV=production
DEBUG=False
PORT=3000
FLASK_PORT=5001
FLASK_SECRET_KEY=[from .env]
JWT_SECRET_KEY=[from .env]
GOOGLE_API_KEY=[from .env]
PROJECT_ID=[from .env]
LOCATION=[from .env]
CORS_ORIGINS=https://chat.7mountainsmedia.com
OAUTH_REDIRECT_URI=https://chat.7mountainsmedia.com/auth/callback
```

Click **Apply** and then **Restart Application**

---

## Step 9: Create Logs Directory

In SSH:
```bash
mkdir -p /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/logs
chmod 755 logs
```

---

## Step 10: Verify Deployment

1. **Health Check**: Visit `https://chat.7mountainsmedia.com/api/health`
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "rag-system-unified",
     "node_server": "running",
     "flask_backend": "running"
   }
   ```

2. **Frontend**: Visit `https://chat.7mountainsmedia.com`
   - Should load React chat interface

3. **Authentication**: Click "Login with Google"
   - Should redirect to Google OAuth
   - After login, should redirect back successfully

---

## Troubleshooting

### Build fails with localStorage error
- **Cause**: Node.js 25.x has a localStorage bug
- **Solution**: The `build-wrapper.js` should handle this. If not, switch to Node 22.x in Plesk

### "npm: command not found" in SSH
- **Solution**: Use full path: `/opt/plesk/node/22/bin/npm`

### Application won't start (502 Bad Gateway)
1. Check Plesk logs: Domains → Logs
2. Verify `server.js` exists in application root
3. Check Flask backend: `ps aux | grep python`
4. Verify environment variables are set

### Flask backend not starting
1. Check Python dependencies: `python3 -m pip list | grep flask`
2. Verify credentials: `ls -la credentials.json token.pickle`
3. Check logs: `tail -f logs/*.log`

### OAuth redirect fails
1. Add redirect URI in Google Cloud Console:
   - Go to APIs & Services → Credentials
   - Edit OAuth 2.0 Client
   - Add: `https://chat.7mountainsmedia.com/auth/callback`
2. Verify CORS_ORIGINS in environment variables

---

## Updating the Application

To update after pushing changes to GitHub:

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com
git pull origin feature/easyocr-integration

# If frontend changed:
cd chat-app
./install-and-build.sh

# If backend changed:
python3 -m pip install --user -r requirements-production.txt

# Restart in Plesk
```

---

## Performance Notes

- **First query**: 5-8 seconds (RAG retrieval + LLM generation)
- **Cached queries**: <50ms (99.9% faster)
- **Database**: 2,062 documents across 11 collections (520 MB)
- **Optimizations**: 11 active (Connection Pooling, Redis Cache, Semantic Cache, etc.)

## 5. Upload Required Files (Plesk File Manager or SFTP)

Upload these to `/var/www/vhosts/7mountainsmedia.com/chat.7mountainsmedia.com/`:
- `credentials.json`
- `token.pickle`
- `.env` (with production URLs)
- `chroma_db/` folder (520 MB - use SFTP/FileZilla)

## 6. Configure Plesk Node.js Application

**Node.js Settings:**
- **Node.js Version:** 18.x or 20.x (NOT 25.x!)
- **Application Root:** `/var/www/vhosts/7mountainsmedia.com/chat.7mountainsmedia.com`
- **Document Root:** `/var/www/vhosts/7mountainsmedia.com/chat.7mountainsmedia.com/chat-app/build`
- **Application Mode:** production
- **Application Startup File:** `server.js`

**Environment Variables (add in Plesk):**
```
FLASK_ENV=production
DEBUG=False
PORT=3000
FLASK_PORT=5001
FLASK_SECRET_KEY=[generate with: python -c "import secrets; print(secrets.token_hex(32))"]
JWT_SECRET_KEY=[generate with: python -c "import secrets; print(secrets.token_hex(32))"]
GOOGLE_API_KEY=[from your .env]
PROJECT_ID=[from your .env]
LOCATION=[from your .env]
CORS_ORIGINS=https://chat.7mountainsmedia.com
OAUTH_REDIRECT_URI=https://chat.7mountainsmedia.com/auth/callback
```

## 7. Create Logs Directory (SSH Terminal)

```bash
mkdir -p /var/www/vhosts/7mountainsmedia.com/chat.7mountainsmedia.com/logs
```

## 8. Restart Application

In Plesk:
1. Go to Node.js settings
2. Click "Restart"

## 9. Verify Deployment

Visit: `https://chat.7mountainsmedia.com/api/health`

Should return:
```json
{
  "status": "healthy",
  "service": "rag-system-unified",
  "node_server": "running",
  "flask_backend": "running"
}
```

## Troubleshooting

**If npm commands fail:**
- Make sure you're in the Node.js terminal (not SSH)
- Try running from Plesk's Node.js interface instead of terminal

**If build fails with localStorage error:**
- Check Node.js version is 18.x or 20.x (NOT 25.x)
- Downgrade in Plesk if needed

**If server won't start:**
- Check Plesk logs: Domains → chat.7mountainsmedia.com → Logs
- Verify all environment variables are set
- Ensure `chat-app/build/` directory exists

**If 502 Bad Gateway:**
- Flask backend isn't starting
- Check Python dependencies are installed
- Verify credentials.json and token.pickle exist
