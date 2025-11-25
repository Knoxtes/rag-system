# 🚀 Deployment Checklist
## For: ask.7mountainsmedia.com
## Plesk Obsidian 18.0.73 | AlmaLinux 9.7 | Node.js 25.2.0

---

## Pre-Deployment Checklist

### ☐ Google Cloud Configuration

- [ ] Google Cloud Project created
- [ ] Vertex AI API enabled
- [ ] Document AI API enabled
- [ ] Google Drive API enabled
- [ ] Service Account created
- [ ] **credentials.json** downloaded
- [ ] OAuth 2.0 Client ID created
- [ ] OAuth redirect URI added: `https://ask.7mountainsmedia.com/auth/callback`
- [ ] Google API key generated

### ☐ Required Files Prepared

- [ ] **credentials.json** (Google Cloud Service Account)
- [ ] **token.pickle** (if you have it from local testing)
- [ ] **.env** file configured with production values
- [ ] **chroma_db/** folder ready to upload (520MB)

### ☐ Security Configuration

- [ ] Generated `FLASK_SECRET_KEY` (32-byte hex string)
- [ ] Generated `JWT_SECRET_KEY` (32-byte hex string)
- [ ] Updated `OAUTH_REDIRECT_URI` to production domain
- [ ] Set `ALLOWED_DOMAINS` to `7mountainsmedia.com`
- [ ] Verified no default/placeholder values in `.env`
- [ ] Confirmed `.env`, `credentials.json`, `token.pickle` in `.gitignore`

---

## Deployment Steps

### ☐ 1. Server Access & Git Setup

- [ ] SSH access to server confirmed
- [ ] Git installed on server
- [ ] GitHub repository access configured
- [ ] Git credentials configured (SSH key or HTTPS)

```bash
ssh user@7mountainsmedia.com
cd /var/www/vhosts/7mountainsmedia.com/ask.7mountainsmedia.com
git clone https://github.com/Knoxtes/rag-system.git .
```

### ☐ 2. Node.js Configuration in Plesk

- [ ] Navigated to: Domains → ask.7mountainsmedia.com → Node.js
- [ ] Clicked "Enable Node.js"
- [ ] Selected Node.js version: **25.2.0**
- [ ] Set Application mode: **production**
- [ ] Set Application root: `/var/www/vhosts/7mountainsmedia.com/ask.7mountainsmedia.com`
- [ ] Set Document root: `/var/www/vhosts/7mountainsmedia.com/ask.7mountainsmedia.com/chat-app/build`
- [ ] Set Application startup file: **server.js**
- [ ] Clicked "Apply" (don't start yet)

### ☐ 3. Environment Configuration

- [ ] Uploaded `.env` file to application root
- [ ] Uploaded `credentials.json` to application root
- [ ] Uploaded `token.pickle` to application root (if available)
- [ ] Verified file permissions (644 for files, 755 for directories)

```bash
chmod 644 .env credentials.json token.pickle
```

### ☐ 4. Run Deployment Script

- [ ] Made deployment script executable
- [ ] Ran deployment script
- [ ] Verified all dependencies installed successfully
- [ ] Confirmed React build completed
- [ ] Checked for any error messages

```bash
chmod +x deploy-plesk.sh
./deploy-plesk.sh
```

### ☐ 5. Upload Large Files (SFTP)

- [ ] Connected via SFTP (FileZilla or similar)
- [ ] Uploaded `chroma_db/` folder (520MB)
- [ ] Verified upload completed successfully
- [ ] Confirmed directory structure intact

### ☐ 6. Configure Environment Variables in Plesk

Navigated to: Domains → ask.7mountainsmedia.com → Node.js → Environment Variables

Added all variables (click "+ Add Variable" for each):

- [ ] `FLASK_ENV` = `production`
- [ ] `DEBUG` = `False`
- [ ] `NODE_ENV` = `production`
- [ ] `LOG_LEVEL` = `INFO`
- [ ] `PORT` = `3000`
- [ ] `FLASK_PORT` = `5001`
- [ ] `FLASK_SECRET_KEY` = `<your-generated-key>`
- [ ] `JWT_SECRET_KEY` = `<your-generated-key>`
- [ ] `GOOGLE_API_KEY` = `<your-api-key>`
- [ ] `GOOGLE_CLIENT_ID` = `<your-client-id>`
- [ ] `GOOGLE_CLIENT_SECRET` = `<your-client-secret>`
- [ ] `PROJECT_ID` = `rag-chatbot-475316`
- [ ] `LOCATION` = `us-central1`
- [ ] `CORS_ORIGINS` = `https://ask.7mountainsmedia.com`
- [ ] `OAUTH_REDIRECT_URI` = `https://ask.7mountainsmedia.com/auth/callback`
- [ ] `ALLOWED_DOMAINS` = `7mountainsmedia.com`
- [ ] Clicked "Apply"

### ☐ 7. Start Application

- [ ] In Plesk Node.js settings, clicked "Restart App"
- [ ] Waited 15-20 seconds for both servers to start
- [ ] No immediate errors in Plesk logs

---

## Verification Steps

### ☐ 8. Health Check

- [ ] Visited: https://ask.7mountainsmedia.com/api/health
- [ ] Received response with `"status": "healthy"`
- [ ] Confirmed `"node_server": "running"`
- [ ] Confirmed `"flask_backend": "healthy"`
- [ ] Confirmed `"rag_initialized": true`

**Expected Response:**
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

### ☐ 9. Frontend Access

- [ ] Visited: https://ask.7mountainsmedia.com
- [ ] Chat interface loaded successfully
- [ ] No console errors in browser developer tools
- [ ] Dark theme displayed correctly
- [ ] UI is responsive

### ☐ 10. Authentication Test

- [ ] Clicked "Login with Google" button
- [ ] Redirected to Google OAuth consent screen
- [ ] Selected @7mountainsmedia.com account
- [ ] Granted permissions
- [ ] Redirected back to ask.7mountainsmedia.com
- [ ] Successfully authenticated
- [ ] User info displayed in UI

### ☐ 11. Chat Functionality Test

- [ ] Typed test query: "What is our vacation policy?"
- [ ] Received response within 5-10 seconds
- [ ] Response includes relevant information
- [ ] Response includes source citations
- [ ] Asked same question again
- [ ] Received cached response in <50ms
- [ ] Verified "Google Drive Browser" tab works
- [ ] Tested file search functionality

### ☐ 12. Log Verification

SSH into server and check logs:

- [ ] Checked application logs: `tail -f logs/rag_system.log`
- [ ] No critical errors in logs
- [ ] Flask backend startup messages present
- [ ] Node.js server startup messages present
- [ ] Checked Plesk logs: Domains → ask.7mountainsmedia.com → Logs
- [ ] No 502 or 500 errors

---

## Post-Deployment Configuration

### ☐ 13. Performance Monitoring

- [ ] Visited: https://ask.7mountainsmedia.com/api/stats
- [ ] Cache hit rates visible
- [ ] System statistics displaying correctly

### ☐ 14. SSL/HTTPS Verification

- [ ] HTTPS working correctly
- [ ] No mixed content warnings
- [ ] SSL certificate valid
- [ ] Green padlock in browser

### ☐ 15. DNS & Domain

- [ ] Domain resolves correctly
- [ ] www redirect configured (if needed)
- [ ] No DNS propagation issues

---

## Optional Enhancements

### ☐ 16. Monitoring & Alerts (Optional)

- [ ] Set up uptime monitoring (e.g., UptimeRobot)
- [ ] Configure email alerts for downtime
- [ ] Set up log monitoring/aggregation

### ☐ 17. Backup Strategy (Optional)

- [ ] Automated database backups configured
- [ ] `.env` file backed up securely
- [ ] `credentials.json` backed up securely
- [ ] `chroma_db/` backup strategy in place

### ☐ 18. Rate Limiting (Optional)

- [ ] Verified rate limiting is working
- [ ] Tested with multiple rapid requests
- [ ] Confirmed rate limit errors return correctly

---

## Troubleshooting Checklist

If any issues occur:

### Application Won't Start

- [ ] Checked Plesk logs for errors
- [ ] Verified Node.js version is 25.2.0
- [ ] Confirmed all environment variables set
- [ ] Checked `server.js` exists in application root
- [ ] Verified `chat-app/build/` directory exists

### OAuth Fails

- [ ] Verified redirect URI matches exactly in Google Cloud Console
- [ ] Confirmed no trailing slashes in redirect URI
- [ ] Checked `OAUTH_REDIRECT_URI` in environment variables
- [ ] Verified HTTPS (not HTTP)

### Chat Not Working

- [ ] Checked Flask backend is running: `ps aux | grep chat_api`
- [ ] Verified `credentials.json` exists
- [ ] Confirmed `chroma_db/` folder uploaded correctly
- [ ] Checked backend logs: `tail -f logs/chat_api.log`

### Frontend Not Loading

- [ ] Verified `chat-app/build/index.html` exists
- [ ] Rebuilt frontend: `cd chat-app && ./install-and-build.sh`
- [ ] Checked document root setting in Plesk
- [ ] Cleared browser cache

---

## Final Verification

### ☐ Complete System Test

- [ ] Logged in as a test user
- [ ] Searched for documents
- [ ] Asked multiple questions
- [ ] Verified performance (first query: 5-8s, cached: <50ms)
- [ ] Tested Google Drive browser
- [ ] Searched for specific files
- [ ] Logged out successfully
- [ ] Logged back in successfully

---

## Documentation Review

- [ ] Read [PLESK_DEPLOYMENT_GUIDE.md](PLESK_DEPLOYMENT_GUIDE.md) thoroughly
- [ ] Reviewed [README.md](README.md) for features and usage
- [ ] Bookmarked troubleshooting section
- [ ] Saved deployment credentials securely (not in git!)

---

## Success Criteria

All checks must pass:

✅ **Health endpoint returns healthy**
✅ **Frontend loads without errors**
✅ **OAuth authentication works**
✅ **Chat responds to queries**
✅ **Cached queries return in <50ms**
✅ **No critical errors in logs**
✅ **HTTPS working correctly**
✅ **All environment variables set**

---

## Contact Information

**For Support:**
- Check troubleshooting guide: [PLESK_DEPLOYMENT_GUIDE.md](PLESK_DEPLOYMENT_GUIDE.md#troubleshooting)
- Review logs: `tail -f logs/rag_system.log`
- GitHub Repository: https://github.com/Knoxtes/rag-system

---

## Deployment Complete! 🎉

**Your RAG System is now live at**: https://ask.7mountainsmedia.com

**System Version**: 2.0.0  
**Deployment Date**: November 21, 2025  
**Platform**: Plesk Obsidian 18.0.73 | AlmaLinux 9.7 | Node.js 25.2.0

---

## Next Steps

1. **Train Users**: Share the application URL with your team
2. **Monitor Performance**: Check logs and health endpoint regularly
3. **Update As Needed**: Use `./update-from-git.sh` for updates
4. **Maintain Backups**: Regular backups of database and credentials
5. **Review Analytics**: Monitor usage patterns and performance

**🚀 Enjoy your production-ready RAG system!**
