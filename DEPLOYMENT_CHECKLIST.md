# Deployment Checklist for Ask.7MountainsMedia.com

## Pre-Deployment Preparation

### Local Development (Complete Before Deployment)
- [ ] All code changes committed and pushed to GitHub
- [ ] Local testing completed successfully
- [ ] Dependencies updated and verified
- [ ] Documentation updated if needed
- [ ] `.gitignore` configured properly (node_modules, build/, credentials)

### Credentials & Configuration Files
- [ ] `credentials.json` - Google Cloud service account JSON file
- [ ] `token.pickle` - Google OAuth token (or will be generated)
- [ ] `.env` file created with production values (see template below)
- [ ] Secret keys generated (FLASK_SECRET_KEY, JWT_SECRET_KEY)
- [ ] Google Cloud Console OAuth redirect URI configured

### Vector Database (If Migrating)
- [ ] `chroma_db/` folder backed up
- [ ] Database size verified (typically ~520MB)
- [ ] Ready for SFTP upload

---

## Plesk Server Setup

### 1. SSH Access & Repository
- [ ] SSH access to server verified
- [ ] Navigate to: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com`
- [ ] Clone repository: `git clone https://github.com/Knoxtes/rag-system.git .`
- [ ] Or pull latest: `git pull origin main`

### 2. Run Automated Setup
- [ ] Make script executable: `chmod +x setup-plesk.sh`
- [ ] Run setup script: `./setup-plesk.sh`
- [ ] Verify Python dependencies installed
- [ ] Verify Node.js dependencies installed
- [ ] Verify React build completed successfully
- [ ] Note any missing files reported

### 3. Upload Required Files
Via Plesk File Manager or SFTP to application root:
- [ ] Upload `credentials.json`
- [ ] Upload `token.pickle` (if available)
- [ ] Upload `.env` with production configuration
- [ ] Upload `chroma_db/` folder (if migrating data)

### 4. Environment Configuration (.env)
Create `.env` in application root with these values:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_SECRET_KEY=<generated-secret-key>
JWT_SECRET_KEY=<generated-secret-key>

# Server Configuration
PORT=3000
FLASK_PORT=5001

# Domain Configuration
DOMAIN=Ask.7MountainsMedia.com
CORS_ORIGINS=https://Ask.7MountainsMedia.com
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback

# Google Cloud Configuration
GOOGLE_API_KEY=<your-api-key>
PROJECT_ID=<your-project-id>
LOCATION=us-central1

# Performance
MAX_WORKERS=4
CACHE_EXPIRY=21600
ENABLE_REDIS_CACHE=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/rag-system.log
```

**Generate Secret Keys:**
```bash
python3 -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

---

## Plesk Configuration

### 5. Enable Node.js in Plesk
Navigate to: **Domains → Ask.7MountainsMedia.com → Node.js**

- [ ] Enable Node.js for domain
- [ ] Select Node.js version: **22.x** (recommended) or 20.x
- [ ] Set Application mode: **production**
- [ ] Set Application Root: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com`
- [ ] Set Document Root: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app/build`
- [ ] Set Application Startup File: `server.js`
- [ ] Click **Apply**

### 6. Configure Environment Variables
In Plesk Node.js settings, add these environment variables:

- [ ] `FLASK_ENV` = `production`
- [ ] `NODE_ENV` = `production`
- [ ] `DEBUG` = `False`
- [ ] `PORT` = `3000`
- [ ] `FLASK_PORT` = `5001`
- [ ] `DOMAIN` = `Ask.7MountainsMedia.com`
- [ ] `CORS_ORIGINS` = `https://Ask.7MountainsMedia.com`
- [ ] `OAUTH_REDIRECT_URI` = `https://Ask.7MountainsMedia.com/auth/callback`

**Note**: Sensitive keys (API keys, secret keys) are loaded from `.env` file for security.

### 7. Directory Permissions
- [ ] `logs/` directory exists and is writable (755)
- [ ] `tmp/` directory exists and is writable (755)
- [ ] `chroma_db/` directory exists and is readable (755)
- [ ] Application root readable by Plesk user

---

## Google Cloud Console Configuration

### 8. OAuth Credentials
Navigate to: **Google Cloud Console → APIs & Services → Credentials**

- [ ] OAuth 2.0 Client ID configured
- [ ] Authorized redirect URI added: `https://Ask.7MountainsMedia.com/auth/callback`
- [ ] Authorized JavaScript origins added: `https://Ask.7MountainsMedia.com`
- [ ] OAuth consent screen configured
- [ ] Test users added (if in testing mode)

### 9. API Enablement
Verify these APIs are enabled:

- [ ] Google Drive API
- [ ] Google Gemini API
- [ ] Vertex AI API
- [ ] Document AI API (if using OCR)

---

## Application Startup & Testing

### 10. Start Application
In Plesk Node.js settings:
- [ ] Click **"Restart App"** button
- [ ] Wait 30 seconds for services to initialize
- [ ] Check Plesk logs for errors (if any)

### 11. Health Check
Visit: `https://Ask.7MountainsMedia.com/api/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "rag-system-unified",
  "node_server": "running",
  "flask_backend": "running",
  "rag_initialized": true
}
```

- [ ] Health endpoint returns 200 OK
- [ ] `node_server` status is "running"
- [ ] `flask_backend` status is "running"
- [ ] `rag_initialized` is true

### 12. Frontend Verification
Visit: `https://Ask.7MountainsMedia.com`

- [ ] Page loads without errors
- [ ] Dark theme UI displays correctly
- [ ] Chat interface is visible
- [ ] Login button is present
- [ ] No console errors in browser DevTools

### 13. Authentication Test
- [ ] Click "Login with Google"
- [ ] OAuth consent screen loads
- [ ] Successful authentication
- [ ] Redirect back to `https://Ask.7MountainsMedia.com/auth/callback`
- [ ] User session established
- [ ] Chat interface accessible

### 14. Functionality Test
- [ ] Collections list loads
- [ ] Can select a collection
- [ ] Can send a test query
- [ ] Response received within 5 seconds
- [ ] Source citations displayed
- [ ] Response formatting correct (markdown)

### 15. Performance Test
- [ ] First query response time: < 8 seconds
- [ ] Cached query response time: < 100ms
- [ ] Page load time: < 3 seconds
- [ ] No memory leaks after multiple queries
- [ ] Backend logs show no errors

---

## Post-Deployment Monitoring

### 16. Log Monitoring (First 24 Hours)
Check logs regularly:
```bash
# Application logs
tail -f /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/logs/rag-system.log

# Plesk error logs
# Domains → Ask.7MountainsMedia.com → Logs
```

- [ ] No critical errors in application logs
- [ ] No 500 errors in Plesk access logs
- [ ] Flask backend running continuously
- [ ] No memory warnings
- [ ] OAuth flows completing successfully

### 17. Resource Monitoring
```bash
# Memory usage
free -h

# Disk space
df -h

# Process status
ps aux | grep -E "node|python"
```

- [ ] Memory usage within expected range (< 2GB)
- [ ] Disk space sufficient (> 5GB free)
- [ ] Node.js process running
- [ ] Python process running

### 18. Security Verification
- [ ] No credentials in logs
- [ ] HTTPS enforced (not HTTP)
- [ ] CORS properly configured
- [ ] OAuth only allows authorized domains
- [ ] Rate limiting working (if enabled)

---

## Troubleshooting Reference

### Common Issues

**502 Bad Gateway:**
- Check Flask backend: `ps aux | grep python`
- Verify credentials: `ls -la credentials.json`
- Check logs: `tail -f logs/*.log`

**Build Dependencies Missing:**
- Install dependencies: `cd chat-app && npm install`
- Rebuild React: `npm run build`
- Node.js 25.x is fully supported with automatic compatibility wrapper

**OAuth Redirect Fails:**
- Verify redirect URI in Google Cloud Console
- Check CORS_ORIGINS in .env
- Clear browser cache and try again

**Build Fails:**
- Check Node.js version: `node --version`
- Clear npm cache: `npm cache clean --force`
- Reinstall dependencies: `npm install`

---

## Rollback Plan

If deployment fails:

1. **Identify Issue:**
   - Check logs: `tail -f logs/*.log`
   - Check Plesk logs
   - Verify health endpoint

2. **Quick Fixes:**
   - Restart application in Plesk
   - Verify environment variables
   - Check file permissions

3. **Full Rollback:**
   ```bash
   cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
   git log --oneline -5  # View recent commits
   git checkout <previous-commit>
   npm run build
   # Restart in Plesk
   ```

---

## Success Criteria

All items must be checked for successful deployment:

- [ ] Health endpoint returns healthy status
- [ ] Frontend loads without errors
- [ ] Authentication works end-to-end
- [ ] Chat functionality operational
- [ ] Response times acceptable
- [ ] No errors in logs
- [ ] Resources within limits
- [ ] Security measures verified

---

## Next Steps After Deployment

### Optimization (Optional)
- [ ] Enable Redis caching for better performance
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Set up monitoring alerts
- [ ] Optimize vector database

### Documentation
- [ ] Update internal documentation
- [ ] Document any custom configurations
- [ ] Note any issues encountered and solutions

### Maintenance
- [ ] Schedule regular dependency updates
- [ ] Plan for database maintenance
- [ ] Set up backup schedule
- [ ] Configure monitoring tools

---

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Version:** _____________  
**Notes:** _____________

---

**Status:** ✅ Ready for production deployment  
**Target:** Ask.7MountainsMedia.com  
**Platform:** Plesk Obsidian 18.0.73 + AlmaLinux 9.7
