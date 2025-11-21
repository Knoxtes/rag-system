# RAG System - Quick Start Guide
## For Ask.7MountainsMedia.com

This is the fastest way to get the RAG System up and running.

---

## 📋 Prerequisites Checklist

Before you start, ensure you have:

- [ ] SSH access to Plesk server
- [ ] Git installed on the server
- [ ] Python 3.8+ installed
- [ ] Node.js 25.2.0 configured in Plesk
- [ ] Google Cloud credentials (`credentials.json`)
- [ ] Domain configured in Plesk (Ask.7MountainsMedia.com)

---

## 🚀 Quick Installation (5 Steps)

### Step 1: Clone Repository

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
git clone https://github.com/Knoxtes/rag-system.git .
```

### Step 2: Run Verification

```bash
bash verify-setup.sh
```

This will check if your environment is ready. Fix any critical errors before proceeding.

### Step 3: Create Environment File

```bash
cp .env.example .env
nano .env  # Edit with your configuration
```

**Required settings in `.env`:**
```bash
FLASK_SECRET_KEY=[generate with: python3 -c "import secrets; print(secrets.token_hex(32))"]
JWT_SECRET_KEY=[generate with: python3 -c "import secrets; print(secrets.token_hex(32))"]
GOOGLE_API_KEY=your_google_api_key
PROJECT_ID=your_gcp_project_id
CORS_ORIGINS=https://Ask.7MountainsMedia.com
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback
```

### Step 4: Run Deployment Script

```bash
bash deploy.sh
```

This will:
- Install all Node.js dependencies
- Install all Python dependencies
- Build the React frontend
- Create necessary directories

### Step 5: Upload Credentials

Upload `credentials.json` to the project root via SFTP or Plesk File Manager.

---

## ⚙️ Plesk Configuration

### Configure Node.js App

1. Go to Plesk → **Domains** → **Ask.7MountainsMedia.com** → **Node.js**
2. Set the following:
   - **Node.js Version:** 25.2.0
   - **Application Mode:** production
   - **Application Root:** `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com`
   - **Document Root:** `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app/build`
   - **Application Startup File:** `server.js`

3. Add Environment Variables (click "Add variable" for each):
   ```
   FLASK_ENV=production
   NODE_ENV=production
   PORT=3000
   FLASK_PORT=5001
   CORS_ORIGINS=https://Ask.7MountainsMedia.com
   ```

4. Click **Apply** and then **Restart Application**

---

## ✅ Verify Deployment

### Test Health Endpoint

```bash
curl https://Ask.7MountainsMedia.com/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "rag-system-unified",
  "node_server": "running",
  "flask_backend": "running"
}
```

### Visit Frontend

Open browser: `https://Ask.7MountainsMedia.com`

You should see the chat interface.

---

## 🐛 Quick Troubleshooting

### Build Fails

```bash
cd chat-app
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Flask Not Starting

```bash
python3 -m pip install --user -r requirements-production.txt
```

### Can't Access Frontend

- Check if build directory exists: `ls -la chat-app/build/`
- If missing, run: `npm run build`

### OAuth Issues

- Verify redirect URI in Google Cloud Console: `https://Ask.7MountainsMedia.com/auth/callback`
- Check CORS_ORIGINS in Plesk environment variables

---

## 📖 Need More Help?

For detailed documentation, see:
- **[PLESK_SETUP_GUIDE.md](PLESK_SETUP_GUIDE.md)** - Complete setup guide
- **[README.md](README.md)** - Project overview
- **[docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md)** - Pre-deployment checklist

---

## 🔄 Updating the Application

When you push changes to GitHub:

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
git pull origin main
bash deploy.sh
```

Then restart the application in Plesk.

---

**Questions?** Check the troubleshooting section in [PLESK_SETUP_GUIDE.md](PLESK_SETUP_GUIDE.md)
