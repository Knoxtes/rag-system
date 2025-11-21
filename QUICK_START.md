# ⚡ Quick Start Guide
## Deploy RAG System to Plesk in 15 Minutes

### For: Ask.7MountainsMedia.com | Node.js 25.2.0

---

## Prerequisites (5 minutes)

✅ **Have These Ready:**
1. Google Cloud credentials.json
2. Generated secret keys (see below)
3. SSH access to Plesk server
4. Git credentials

**Generate Secret Keys:**
```bash
python3 -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

Save these keys - you'll need them in step 3.

---

## Deployment (10 minutes)

### Step 1: Clone & Deploy (3 min)

SSH into your server:
```bash
ssh user@7mountainsmedia.com
cd /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com
git clone https://github.com/Knoxtes/rag-system.git .
chmod +x deploy-plesk.sh
./deploy-plesk.sh
```

Wait for the script to complete.

---

### Step 2: Configure .env (2 min)

Edit the `.env` file:
```bash
nano .env
```

Update these critical values:
```env
FLASK_SECRET_KEY=<paste-your-generated-key>
JWT_SECRET_KEY=<paste-your-generated-key>
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_API_KEY=<your-api-key>
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback
CORS_ORIGINS=https://Ask.7MountainsMedia.com
```

Save and exit (Ctrl+X, Y, Enter).

---

### Step 3: Enable Node.js in Plesk (3 min)

1. Open Plesk → **Domains** → **Ask.7MountainsMedia.com**
2. Click **Node.js** in sidebar
3. Click **Enable Node.js**
4. Configure:
   - Node.js version: `25.2.0`
   - Application mode: `production`
   - Application root: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com`
   - Document root: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/chat-app/build`
   - Startup file: `server.js`
5. Click **Apply**

---

### Step 4: Set Environment Variables in Plesk (2 min)

In Plesk Node.js settings, click **Environment Variables**.

Add these (minimum required):
```
FLASK_ENV=production
NODE_ENV=production
PORT=3000
FLASK_PORT=5001
FLASK_SECRET_KEY=<your-key>
JWT_SECRET_KEY=<your-key>
GOOGLE_API_KEY=<your-key>
PROJECT_ID=rag-chatbot-475316
LOCATION=us-central1
CORS_ORIGINS=https://Ask.7MountainsMedia.com
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback
```

Click **Apply**.

---

### Step 5: Start Application (1 min)

In Plesk Node.js settings:
- Click **Restart App**
- Wait 15 seconds

---

## Verify (2 minutes)

### 1. Health Check
Visit: https://Ask.7MountainsMedia.com/api/health

Should see:
```json
{
  "status": "healthy",
  "node_server": "running",
  "flask_backend": "healthy"
}
```

### 2. Frontend
Visit: https://Ask.7MountainsMedia.com

Should see the chat interface.

### 3. Test Login
Click "Login with Google" → Complete OAuth → Should be authenticated.

---

## ✅ Done!

**Your RAG system is live!**

---

## Need More Details?

📖 **Complete Guide**: [PLESK_DEPLOYMENT_GUIDE.md](PLESK_DEPLOYMENT_GUIDE.md)  
📋 **Full Checklist**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)  
🐛 **Troubleshooting**: [PLESK_DEPLOYMENT_GUIDE.md#troubleshooting](PLESK_DEPLOYMENT_GUIDE.md#troubleshooting)

---

## Common Issues

**502 Bad Gateway?**
- Check Plesk logs
- Restart application in Plesk

**OAuth fails?**
- Verify redirect URI in Google Cloud Console
- Must be: `https://Ask.7MountainsMedia.com/auth/callback`

**Frontend not loading?**
- Check if build directory exists: `ls chat-app/build/`
- Rebuild: `cd chat-app && ./install-and-build.sh`

---

## Quick Commands

```bash
# Update from git
./update-from-git.sh

# View logs
tail -f logs/rag_system.log

# Check health
curl https://Ask.7MountainsMedia.com/api/health

# Rebuild frontend
cd chat-app && ./install-and-build.sh
```

---

**🚀 15-minute deployment complete!**

*For production optimization and advanced features, see the complete documentation.*
