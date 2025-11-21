# Plesk Manual Setup Guide

Since Plesk's Node.js terminal runs from `/chat-app` directory by default, follow these steps:

## 1. Install Python Dependencies (SSH Terminal)

In Plesk SSH terminal:
```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com
python3 -m pip install --user -r requirements-production.txt
```

## 2. Install Root Node.js Dependencies (SSH Terminal)

In SSH terminal (not Node.js terminal):
```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com
npm install
```

## 3. Install React Dependencies (Plesk Node.js Terminal)

Plesk Node.js terminal already starts in `/chat-app`, so just run:
```bash
npm install --ignore-scripts
```

The `--ignore-scripts` flag prevents the Node 25.x localStorage error.

## 4. Build React App (Plesk Node.js Terminal)

Still in Plesk Node.js terminal:
```bash
npm run build
```

If you get the localStorage error, the build wrapper should handle it automatically.

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
