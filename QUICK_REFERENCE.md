# Quick Reference Guide - Ask.7MountainsMedia.com

## Essential Commands

### Initial Deployment
```bash
# Clone repository
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
git clone https://github.com/Knoxtes/rag-system.git .

# Run automated setup
chmod +x setup-plesk.sh
./setup-plesk.sh
```

### Updates & Maintenance
```bash
# Pull latest changes
git pull origin main

# Rebuild React app (if frontend changed)
cd chat-app
/opt/plesk/node/22/bin/npm install
/opt/plesk/node/22/bin/npm run build

# Update Python dependencies (if backend changed)
python3 -m pip install --user -r requirements-linux.txt

# Then restart in Plesk Node.js settings
```

### Troubleshooting
```bash
# View logs
tail -f logs/rag-system.log
tail -f /var/log/plesk/error_log

# Check running processes
ps aux | grep -E "node|python"

# Check ports
lsof -i :3000
lsof -i :5001

# Test Python backend directly
python3 chat_api.py --port 5001

# Verify credentials exist
ls -la credentials.json token.pickle .env
```

## Important URLs

- **Frontend**: https://Ask.7MountainsMedia.com
- **Health Check**: https://Ask.7MountainsMedia.com/api/health
- **OAuth Callback**: https://Ask.7MountainsMedia.com/auth/callback

## Key Configuration Values

### Plesk Node.js Settings
- **Node.js Version**: 22.x (recommended) or 20.x
- **Application Root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com`
- **Document Root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app/build`
- **Startup File**: `server.js`
- **Application Mode**: `production`

### Environment Variables (.env)
```bash
DOMAIN=Ask.7MountainsMedia.com
CORS_ORIGINS=https://Ask.7MountainsMedia.com
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback
FLASK_ENV=production
PORT=3000
FLASK_PORT=5001
```

## Quick Checks

### Health Status
```bash
curl https://Ask.7MountainsMedia.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "node_server": "running",
  "flask_backend": "running",
  "rag_initialized": true
}
```

### Build Verification
```bash
# Check build exists
ls -la chat-app/build/index.html

# Check build size
du -sh chat-app/build/
```

### Service Status
```bash
# Check if services are running
ps aux | grep "node.*server.js"
ps aux | grep "python.*chat_api"

# Check memory usage
free -h

# Check disk space
df -h
```

## Common Issues & Solutions

### Issue: 502 Bad Gateway
**Solution**: Flask backend not running
```bash
ps aux | grep python | grep chat_api
# If not found, restart in Plesk
```

### Issue: OAuth Fails
**Solution**: Check redirect URI in Google Cloud Console
- Must be: `https://Ask.7MountainsMedia.com/auth/callback`
- Verify CORS_ORIGINS in .env matches

### Issue: Build Fails
**Solution**: Check Node.js version
```bash
/opt/plesk/node/22/bin/node --version
# Should be 22.x or 20.x, NOT 25.x
```

### Issue: Module Not Found
**Solution**: Reinstall dependencies
```bash
python3 -m pip install --user -r requirements-linux.txt
```

## File Locations

### Application Files
- **Root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com`
- **Logs**: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/logs/`
- **Build**: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app/build/`
- **Vector DB**: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chroma_db/`

### Plesk Managed
- **Node.js**: `/opt/plesk/node/22/`
- **Logs**: Domains → Ask.7MountainsMedia.com → Logs

## Secret Key Generation
```bash
# Generate Flask secret key
python3 -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"

# Generate JWT secret key
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

## Performance Monitoring
```bash
# Real-time log monitoring
tail -f logs/rag-system.log

# Memory usage
free -h

# Disk usage
df -h /var/www/vhosts/7mountainsmedia.com/

# Process monitoring
htop
```

## Backup Commands
```bash
# Backup vector database
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
tar -czf chroma_db_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Backup credentials
tar -czf credentials_backup_$(date +%Y%m%d).tar.gz credentials.json token.pickle .env
```

## Documentation References

- **Full Setup Guide**: [PLESK_ALMALINUX_SETUP.md](PLESK_ALMALINUX_SETUP.md)
- **Deployment Checklist**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Main README**: [README.md](README.md)
- **Deprecated Scripts**: [DEPRECATED_SCRIPTS.md](DEPRECATED_SCRIPTS.md)

---

**Last Updated**: November 2025  
**Platform**: Plesk Obsidian 18.0.73 + AlmaLinux 9.7  
**Domain**: Ask.7MountainsMedia.com
