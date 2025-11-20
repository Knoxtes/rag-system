# Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the optimized RAG system to production.

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher
- **Memory**: Minimum 4GB RAM recommended
- **Disk Space**: 10GB free space minimum
- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows Server

### Required Accounts & Services
- Google Cloud Project with billing enabled
- Google OAuth 2.0 credentials configured
- Google Drive API enabled
- Vertex AI API enabled (for production AI features)

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/Knoxtes/rag-system.git
cd rag-system
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install production dependencies
pip install -r requirements-production.txt
```

### 3. Set Up Node.js Environment
```bash
# Install backend dependencies (for unified server)
npm install

# Install frontend dependencies
cd chat-app
npm install
npm run build
cd ..
```

### 4. Configure Environment Variables

Copy the example environment file and configure it:
```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Required Production Variables
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
JWT_SECRET_KEY=your_secure_random_key_32_chars_min
FLASK_SECRET_KEY=your_flask_secret_32_chars_min
GOOGLE_API_KEY=your_google_api_key
PROJECT_ID=your_google_cloud_project

# Security Settings (IMPORTANT!)
FLASK_ENV=production
ALLOWED_DOMAINS=yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# Application Settings
PORT=5000
HOST=0.0.0.0
```

**Generate secure keys:**
```bash
# Generate JWT secret
python -c 'import secrets; print(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}")'

# Generate Flask secret
python -c 'import secrets; print(f"FLASK_SECRET_KEY={secrets.token_urlsafe(32)}")'
```

### 5. Set Up Google Cloud Credentials

#### Option A: OAuth Web Application (Recommended)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to APIs & Services > Credentials
3. Create OAuth 2.0 Client ID (Web application type)
4. Add authorized redirect URIs:
   - `https://yourdomain.com/auth/callback`
   - `http://localhost:3000/auth/callback` (for testing)
5. Download credentials and set as environment variables

#### Option B: Service Account (For backend only)
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Save as `credentials.json` in the project root
4. **NEVER commit this file to version control!**

### 6. Validate Configuration

Before starting, validate your configuration:
```bash
python3 config_validator.py
```

This will check all required environment variables and provide clear error messages if anything is missing.

### 7. Initialize Google Drive Authentication

For first-time setup, authenticate with Google Drive:
```bash
python3 auth.py
```

This will open a browser window for OAuth authorization. Complete the flow to generate your token.

### 8. Index Your Documents (Optional)

If you want to index Google Drive folders for RAG search:
```bash
# This is typically done through the admin interface
# Or manually if you have indexed_folders.json configured
```

## Starting the Application

### Development Mode
```bash
# Validates config and starts in development mode
python3 start_production.py
```

### Production Mode
```bash
# Set production environment
export FLASK_ENV=production

# Start with production script (includes validation)
python3 start_production.py

# Or use npm script
npm start
```

### Using Process Manager (Recommended for Production)

#### Using PM2 (Node.js Process Manager)
```bash
# Install PM2 globally
npm install -g pm2

# Start application
pm2 start npm --name "rag-system" -- start

# View logs
pm2 logs rag-system

# Setup auto-restart on reboot
pm2 startup
pm2 save
```

#### Using systemd (Linux)
Create `/etc/systemd/system/rag-system.service`:
```ini
[Unit]
Description=RAG System
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/rag-system
Environment="FLASK_ENV=production"
Environment="PATH=/path/to/venv/bin:$PATH"
ExecStart=/path/to/venv/bin/python3 start_production.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable rag-system
sudo systemctl start rag-system
sudo systemctl status rag-system
```

## Reverse Proxy Setup

### Nginx Configuration
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy to Flask application
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts for long-running AI requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Static files (if serving separately)
    location /static {
        alias /path/to/rag-system/chat-app/build/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Client max body size (for file uploads)
    client_max_body_size 100M;
}
```

### Apache Configuration
```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    Redirect permanent / https://yourdomain.com/
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com

    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /path/to/ssl/certificate.crt
    SSLCertificateKeyFile /path/to/ssl/private.key
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    
    # Security Headers
    Header always set X-Frame-Options "DENY"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

    # Proxy Configuration
    ProxyPreserveHost On
    ProxyPass / http://localhost:5000/
    ProxyPassReverse / http://localhost:5000/
    
    # Timeout for long-running requests
    ProxyTimeout 300

    # Logs
    ErrorLog ${APACHE_LOG_DIR}/rag-system-error.log
    CustomLog ${APACHE_LOG_DIR}/rag-system-access.log combined
</VirtualHost>
```

## SSL/TLS Certificate Setup

### Using Let's Encrypt (Free)
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# For Nginx
sudo certbot --nginx -d yourdomain.com

# For Apache
sudo certbot --apache -d yourdomain.com

# Auto-renewal (already setup by certbot)
sudo certbot renew --dry-run
```

## Firewall Configuration

```bash
# Allow SSH (if using)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Monitoring & Logging

### Application Logs
Logs are stored in `logs/rag_system.log` with automatic rotation.

View logs:
```bash
# Tail logs in real-time
tail -f logs/rag_system.log

# Search for errors
grep ERROR logs/rag_system.log

# If using systemd
sudo journalctl -u rag-system -f
```

### Health Monitoring
The application provides a health endpoint:
```bash
curl https://yourdomain.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "rag_initialized": true,
  "collections_available": 5,
  "auth_required": true
}
```

### Set Up Monitoring Alerts

Create a simple monitoring script (`/usr/local/bin/monitor-rag.sh`):
```bash
#!/bin/bash
HEALTH_URL="http://localhost:5000/health"
ALERT_EMAIL="admin@yourdomain.com"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $response -ne 200 ]; then
    echo "RAG System health check failed with status: $response" | \
        mail -s "RAG System Alert" $ALERT_EMAIL
fi
```

Add to crontab to run every 5 minutes:
```bash
*/5 * * * * /usr/local/bin/monitor-rag.sh
```

## Backup Strategy

### Database Backups
```bash
# Create backup script (/usr/local/bin/backup-rag.sh)
#!/bin/bash
BACKUP_DIR="/backups/rag-system"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup ChromaDB
tar -czf "$BACKUP_DIR/chroma_db_$DATE.tar.gz" \
    /path/to/rag-system/chroma_db/

# Backup credentials (encrypted)
gpg --encrypt --recipient admin@yourdomain.com \
    -o "$BACKUP_DIR/credentials_$DATE.json.gpg" \
    /path/to/rag-system/credentials.json

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.gpg" -mtime +30 -delete
```

Add to crontab for daily backups:
```bash
0 2 * * * /usr/local/bin/backup-rag.sh
```

## Scaling Considerations

### Vertical Scaling
- Increase server RAM for larger vector databases
- Add more CPU cores for concurrent request handling
- Use SSD storage for faster ChromaDB operations

### Horizontal Scaling
For high-traffic deployments:
1. Use a load balancer (nginx, HAProxy)
2. Run multiple application instances
3. Share ChromaDB via network storage (NFS, GlusterFS)
4. Consider Redis for distributed caching

### Database Optimization
- Monitor ChromaDB index size
- Regularly clean up old indexes
- Use collection-based sharding for large datasets

## Security Checklist

- [ ] All environment variables set correctly
- [ ] JWT_SECRET_KEY is strong and unique (32+ chars)
- [ ] FLASK_SECRET_KEY is strong and unique (32+ chars)
- [ ] ALLOWED_DOMAINS configured to restrict access
- [ ] CORS_ORIGINS limited to your domain
- [ ] FLASK_ENV=production set
- [ ] SSL/TLS certificates installed and auto-renewing
- [ ] Firewall configured to allow only necessary ports
- [ ] credentials.json never committed to version control
- [ ] File permissions set correctly (600 for sensitive files)
- [ ] Regular security updates applied
- [ ] Monitoring and alerting configured
- [ ] Backups tested and working

## Troubleshooting

### Configuration Validation Fails
```bash
# Run validator with verbose output
python3 config_validator.py

# Check specific environment variable
echo $JWT_SECRET_KEY
```

### Application Won't Start
```bash
# Check logs
tail -f logs/rag_system.log

# Test configuration
python3 -c "from config_validator import validate_environment; validate_environment()"

# Check port availability
sudo lsof -i :5000
```

### Google Drive Authentication Issues
```bash
# Re-authenticate
python3 auth.py

# Check token file exists and is valid
ls -la token.pickle

# Check credentials file
ls -la credentials.json
```

### Memory Issues
```bash
# Check memory usage
free -h

# Monitor application memory
ps aux | grep python

# If using systemd, set memory limits
# Add to service file:
# MemoryLimit=2G
```

### High CPU Usage
- Check for infinite loops in logs
- Monitor ChromaDB query performance
- Consider adding request rate limiting
- Scale horizontally if needed

## Maintenance Tasks

### Daily
- Monitor error logs
- Check application health endpoint
- Verify backup completion

### Weekly
- Review security logs
- Update system packages
- Check disk space usage

### Monthly
- Review and rotate logs
- Test backup restoration
- Security audit
- Performance optimization review

### Quarterly
- Update dependencies
- Review and update documentation
- Disaster recovery drill
- Capacity planning review

## Support & Documentation

- **Application Docs**: See README.md and other .md files in project
- **API Documentation**: Available at `/api/docs` when running
- **Configuration**: See .env.example for all options
- **Optimization Report**: See OPTIMIZATION_REPORT.md

## Emergency Procedures

### Application Crash
```bash
# If using PM2
pm2 restart rag-system

# If using systemd
sudo systemctl restart rag-system

# Check logs immediately
tail -100 logs/rag_system.log
```

### Database Corruption
```bash
# Stop application
sudo systemctl stop rag-system

# Restore from backup
cd /path/to/rag-system
rm -rf chroma_db/
tar -xzf /backups/rag-system/chroma_db_latest.tar.gz

# Restart application
sudo systemctl start rag-system
```

### Security Breach Suspected
1. Immediately take application offline
2. Review all logs for suspicious activity
3. Rotate all secrets (JWT, Flask, API keys)
4. Force re-authentication for all users
5. Audit all system access
6. Contact security team/expert

## Conclusion

Your RAG system is now production-ready with:
- Comprehensive security measures
- Input validation and sanitization
- Configuration validation
- Monitoring and logging
- Backup and recovery procedures
- Performance optimization
- Scalability options

For questions or issues, refer to the troubleshooting section or create an issue in the GitHub repository.

**Production Readiness: ✅ CERTIFIED**
