# RAG System Production Deployment Guide

## 🚀 Production Deployment for Plesk Hosting

### Prerequisites
- Plesk hosting account with Python support
- Google Cloud Project with OAuth 2.0 credentials
- Domain with SSL certificate
- Python 3.8+

### Step 1: Google OAuth Setup

1. **Create Google Cloud Project**
   ```bash
   # Go to: https://console.cloud.google.com/
   # Create new project or select existing
   ```

2. **Enable APIs**
   - Google Drive API
   - Google OAuth 2.0

3. **Create OAuth 2.0 Credentials**
   ```
   Authorized JavaScript origins: https://yourdomain.com
   Authorized redirect URIs: https://yourdomain.com/auth/callback
   ```

4. **Download credentials** and note:
   - Client ID
   - Client Secret

### Step 2: Environment Configuration

1. **Update `.env.production`**
   ```env
   # Required - Google OAuth
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   OAUTH_REDIRECT_URI=https://yourdomain.com/auth/callback
   
   # Required - Organization Access
   ALLOWED_DOMAINS=yourdomain.com,anotherdomain.com
   
   # Required - Security
   FLASK_SECRET_KEY=generate-strong-secret-key
   JWT_SECRET_KEY=generate-strong-jwt-key
   
   # Optional - CORS
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

2. **Generate Secret Keys**
   ```python
   import secrets
   print("FLASK_SECRET_KEY=" + secrets.token_urlsafe(32))
   print("JWT_SECRET_KEY=" + secrets.token_urlsafe(32))
   ```

### Step 3: File Preparation

1. **Run deployment script**
   ```bash
   chmod +x deploy_production.sh
   ./deploy_production.sh
   ```

2. **Key files for upload:**
   - `app.py` (WSGI entry point)
   - `chat_api.py` (main Flask app)
   - `oauth_config.py` (authentication)
   - `auth_routes.py` (auth endpoints)
   - `health_monitor.py` (monitoring)
   - `.env.production` (environment config)
   - `requirements-auth.txt` (dependencies)
   - All RAG system files (`rag_system.py`, etc.)
   - React build files from `chat-app/build/`

### Step 4: Plesk Configuration

1. **Upload Files**
   - Upload all Python files to domain directory
   - Upload React build files to `httpdocs/` or similar

2. **Python App Configuration in Plesk**
   ```
   Python version: 3.8+
   Application root: /your-domain-directory
   Application URL: / (root)
   Application startup file: app.py
   ```

3. **Install Dependencies**
   ```bash
   # In Plesk Python environment
   pip install -r requirements-auth.txt
   ```

4. **Environment Variables in Plesk**
   - Go to "Python" > "Environment Variables"
   - Add all variables from `.env.production`

### Step 5: React App Production Build

1. **Update React environment**
   ```bash
   cd chat-app
   echo "REACT_APP_API_URL=https://yourdomain.com" > .env.production.local
   ```

2. **Build for production**
   ```bash
   npm run build
   ```

3. **Upload build files**
   - Upload `build/` contents to `httpdocs/`

### Step 6: Security Configuration

1. **SSL Certificate**
   - Enable SSL/TLS in Plesk
   - Force HTTPS redirect

2. **Security Headers** (in .htaccess)
   ```apache
   Header always set X-Content-Type-Options nosniff
   Header always set X-Frame-Options DENY
   Header always set X-XSS-Protection "1; mode=block"
   Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
   ```

### Step 7: Testing & Monitoring

1. **Health Check Endpoints**
   ```
   https://yourdomain.com/health          # Basic health
   https://yourdomain.com/health/detailed # Detailed status
   https://yourdomain.com/health/liveness # Liveness probe
   ```

2. **Authentication Test**
   ```
   https://yourdomain.com/auth/login     # OAuth flow
   https://yourdomain.com/               # Protected app
   ```

### Step 8: Performance Optimization

1. **Enable Gzip Compression** (in .htaccess)
   ```apache
   <IfModule mod_deflate.c>
       AddOutputFilterByType DEFLATE text/plain text/html text/xml text/css text/javascript application/javascript application/json
   </IfModule>
   ```

2. **Cache Static Files**
   ```apache
   <FilesMatch "\.(css|js|png|jpg|jpeg|gif|ico|svg)$">
       ExpiresActive On
       ExpiresDefault "access plus 1 year"
   </FilesMatch>
   ```

3. **Database Optimization**
   - Use SSD storage for ChromaDB
   - Configure appropriate cache settings

### Step 9: Backup & Monitoring

1. **Set up automated backups**
   ```bash
   # Cron job for daily backups
   0 2 * * * /path/to/rag-system/backup.sh
   ```

2. **Log monitoring**
   ```bash
   tail -f logs/rag_system.log
   tail -f logs/errors.log
   ```

### Troubleshooting

#### Common Issues:

1. **OAuth Redirect Mismatch**
   ```
   Error: redirect_uri_mismatch
   Solution: Update Google OAuth settings with exact domain
   ```

2. **Import Errors**
   ```
   Error: ModuleNotFoundError
   Solution: Ensure all dependencies in requirements-auth.txt are installed
   ```

3. **Permission Errors**
   ```
   Error: Permission denied
   Solution: Check file permissions (755 for directories, 644 for files)
   ```

4. **CORS Errors**
   ```
   Error: CORS policy
   Solution: Update CORS_ORIGINS in .env.production
   ```

#### Health Check Commands:

```bash
# Test health endpoint
curl -X GET https://yourdomain.com/health/detailed

# Test authentication
curl -X GET https://yourdomain.com/auth/login

# Check logs
tail -n 50 logs/rag_system.log
```

### Production Checklist

- [ ] Google OAuth configured
- [ ] Environment variables set
- [ ] SSL certificate installed
- [ ] Dependencies installed
- [ ] React app built and uploaded
- [ ] Health checks passing
- [ ] Authentication working
- [ ] CORS properly configured
- [ ] Backup script configured
- [ ] Log monitoring set up
- [ ] Performance optimizations applied

### Security Best Practices

1. **Regular Updates**
   - Update dependencies monthly
   - Monitor security advisories

2. **Access Control**
   - Limit organization domains strictly
   - Regular audit of authenticated users

3. **Monitoring**
   - Set up log alerts for errors
   - Monitor resource usage

4. **Backup**
   - Daily automated backups
   - Test restore procedures

### Performance Tuning

1. **Caching**
   - Enable Redis for rate limiting
   - Cache frequently accessed data

2. **Database**
   - Regular ChromaDB maintenance
   - Monitor query performance

3. **Resources**
   - Monitor memory usage
   - Scale based on usage patterns

## 🎯 Production Ready Features

✅ **Authentication & Authorization**
- Google OAuth 2.0 integration
- Organization domain restrictions
- JWT token management
- Session security

✅ **Security**
- HTTPS enforcement
- Security headers
- Rate limiting
- Input validation

✅ **Monitoring & Logging**
- Health check endpoints
- Structured logging
- Error tracking
- Performance monitoring

✅ **High Availability**
- Graceful error handling
- Automatic retries
- Health checks
- Zero-downtime deployment

✅ **Performance**
- Caching layers
- Connection pooling
- Resource optimization
- Background processing