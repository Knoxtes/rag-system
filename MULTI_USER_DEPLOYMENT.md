# Multi-User Production Deployment Guide

## Overview
This RAG system is optimized for multi-user production deployment with enterprise-grade security, performance, and scalability.

## Multi-User Features

### ✅ Concurrent User Support
- **Thread-safe operations**: All database and API operations are thread-safe
- **Session isolation**: Each user has isolated session data with secure cookies
- **Connection pooling**: Efficient Google Drive API connection management
- **Resource sharing**: Intelligent caching shared across users for efficiency

### ✅ Authentication & Authorization
- **OAuth 2.0**: Google OAuth for user authentication
- **Domain restrictions**: Limit access to specific email domains
- **JWT tokens**: Secure token-based authentication (7-day access, 30-day refresh)
- **Session management**: Secure, HttpOnly cookies with SameSite protection

### ✅ Rate Limiting & Security
- **Per-IP rate limiting**: 200 requests/day, 50 requests/hour per IP
- **Security headers**: HSTS, XSS protection, frame denial, content type sniffing prevention
- **Input validation**: Comprehensive request validation
- **CORS protection**: Configurable allowed origins

### ✅ Performance Optimization
- **Multi-layer caching**: Folder, embedding, and query result caching
- **Background tasks**: Non-blocking cache refresh and maintenance
- **Batch operations**: Efficient bulk data loading
- **Memory management**: LRU eviction and intelligent preloading

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Cloud Project with billing enabled
- Minimum 4GB RAM (8GB+ recommended for production)
- 10GB+ disk space

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Knoxtes/rag-system.git
cd rag-system

# Install Python dependencies
pip install -r requirements-unified.txt

# Install Node.js dependencies
npm install
cd chat-app && npm install && cd ..

# Build React frontend
cd chat-app && npm run build && cd ..
```

### Step 2: Configure Environment

Create `.env.production` file:

```env
# Flask Configuration
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=false

# OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=https://your-domain.com/auth/callback

# Domain Restrictions (comma-separated)
ALLOWED_DOMAINS=yourdomain.com,partnerdomain.com

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-here
TOKEN_EXPIRY_HOURS=168
REFRESH_TOKEN_EXPIRY_DAYS=30

# CORS Configuration
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# Rate Limiting (optional overrides)
RATELIMIT_ENABLED=true
RATELIMIT_STORAGE_URL=redis://localhost:6379
```

### Step 3: Set Up Google Cloud

1. **Create Project**
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. **Enable APIs**
   ```bash
   gcloud services enable drive.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable documentai.googleapis.com
   ```

3. **Create OAuth Credentials**
   - Go to Google Cloud Console → APIs & Services → Credentials
   - Create OAuth 2.0 Client ID (Web application)
   - Add authorized redirect URI: `https://your-domain.com/auth/callback`
   - Download credentials as `credentials.json`

4. **Create Service Account** (for Vertex AI)
   ```bash
   gcloud iam service-accounts create rag-system-sa
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:rag-system-sa@your-project-id.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   gcloud iam service-accounts keys create service-account-key.json \
     --iam-account=rag-system-sa@your-project-id.iam.gserviceaccount.com
   ```

### Step 4: Initialize Database

```bash
# Create necessary directories
mkdir -p logs chroma_db embedding_cache csv_cache

# Set permissions (Linux/Mac)
chmod 755 logs chroma_db embedding_cache csv_cache
```

### Step 5: Test Locally

```bash
# Test production mode locally
python passenger_wsgi.py

# Or use the unified server
npm start
```

Visit `http://localhost:3000` and test:
- [ ] Authentication works
- [ ] Can browse Google Drive
- [ ] Can query documents
- [ ] Rate limiting enforces limits
- [ ] Multiple browser sessions work independently

## Production Deployment

### Option 1: Plesk (Recommended)

1. **Upload Files**
   - Upload entire project via FTP/SFTP or Git
   - Ensure `credentials.json` and `.env.production` are uploaded

2. **Configure Python App**
   - Go to Plesk → Python
   - Set Python version: 3.8+
   - Application root: `/path/to/rag-system`
   - Application startup file: `passenger_wsgi.py`
   - Application URL: Your domain

3. **Set Environment Variables**
   - Go to Plesk → Python → Environment Variables
   - Add all variables from `.env.production`

4. **Configure Static Files**
   - Static files directory: `chat-app/build`
   - Static files URL: `/`

5. **Install Dependencies**
   ```bash
   pip install -r requirements-unified.txt
   ```

6. **Restart Application**
   - Click "Restart App" in Plesk control panel

### Option 2: VPS/Dedicated Server

1. **Install System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-dev nginx redis-server
   
   # Install Node.js
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

2. **Set Up Gunicorn**
   ```bash
   # Install Gunicorn
   pip install gunicorn gevent
   
   # Create systemd service
   sudo nano /etc/systemd/system/rag-system.service
   ```

   Service file content:
   ```ini
   [Unit]
   Description=RAG System
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/rag-system
   Environment="PATH=/path/to/rag-system/venv/bin"
   ExecStart=/path/to/rag-system/venv/bin/gunicorn --workers 4 --worker-class gevent --bind 127.0.0.1:5000 passenger_wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

3. **Configure Nginx**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           root /path/to/rag-system/chat-app/build;
           try_files $uri $uri/ /index.html;
       }

       location /api {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /auth {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /chat {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_read_timeout 60s;
       }
   }
   ```

4. **Enable SSL with Let's Encrypt**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

5. **Start Services**
   ```bash
   sudo systemctl enable rag-system
   sudo systemctl start rag-system
   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

### Option 3: Docker (Advanced)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-unified.txt
RUN cd chat-app && npm install && npm run build

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--workers", "4", "--worker-class", "gevent", "--bind", "0.0.0.0:5000", "passenger_wsgi:application"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  rag-system:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./chroma_db:/app/chroma_db
      - ./logs:/app/logs
      - ./embedding_cache:/app/embedding_cache
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
```

## Multi-User Scaling

### For 10-50 Users (Single Server)
- **Resources**: 4GB RAM, 2 CPU cores
- **Configuration**: Default settings
- **Caching**: File-based caching (built-in)
- **Expected costs**: $5-15/month

### For 50-200 Users (Optimized Single Server)
- **Resources**: 8GB RAM, 4 CPU cores
- **Configuration**: 
  - Increase Gunicorn workers: `--workers 8`
  - Enable Redis for caching: `RATELIMIT_STORAGE_URL=redis://localhost:6379`
  - Increase rate limits: `"500 per day", "100 per hour"`
- **Expected costs**: $20-50/month

### For 200+ Users (Multi-Server)
- **Architecture**: Load balancer → Multiple app servers → Shared Redis → Shared Database
- **Resources**: 
  - Load balancer: HAProxy or Nginx
  - App servers: 2-4 servers (8GB RAM each)
  - Redis: Dedicated server (4GB RAM)
  - ChromaDB: Dedicated server with SSD
- **Configuration**:
  - Use Redis for distributed caching
  - Use PostgreSQL for session storage
  - Enable CDN for static files
  - Add monitoring (Prometheus, Grafana)
- **Expected costs**: $200-500/month

## Monitoring & Maintenance

### Health Checks
```bash
# Check service status
curl https://your-domain.com/health

# Expected response
{
  "status": "healthy",
  "rag_initialized": true,
  "collections_available": 5,
  "auth_required": true
}
```

### Log Monitoring
```bash
# View live logs
tail -f logs/production.log

# Search for errors
grep ERROR logs/production.log

# Monitor rate limit violations
grep "rate limit exceeded" logs/production.log
```

### Performance Monitoring
```bash
# Check system stats
python system_stats.py

# Monitor cache hit rates
curl https://your-domain.com/cache/status

# Check API costs
curl https://your-domain.com/cost/summary
```

### Backup Strategy

1. **Daily ChromaDB Backup**
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d)
   tar -czf chroma_db_backup_$DATE.tar.gz chroma_db/
   # Upload to cloud storage
   ```

2. **Weekly Full Backup**
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d)
   tar -czf rag_system_backup_$DATE.tar.gz \
     --exclude='node_modules' \
     --exclude='venv' \
     --exclude='*.pyc' \
     .
   ```

## Troubleshooting

### Issue: High Memory Usage
- **Symptom**: Server running out of memory
- **Solutions**:
  - Reduce cache sizes in `config.py`
  - Decrease Gunicorn workers
  - Add swap space
  - Upgrade server RAM

### Issue: Slow Response Times
- **Symptom**: Users experiencing delays
- **Solutions**:
  - Check cache hit rates
  - Enable Redis caching
  - Optimize ChromaDB queries
  - Add more Gunicorn workers
  - Consider adding load balancer

### Issue: Rate Limit Errors
- **Symptom**: Users getting rate limited
- **Solutions**:
  - Increase rate limits in `rate_limiter.py`
  - Implement user-based (not IP-based) rate limiting
  - Add premium tier with higher limits

### Issue: High API Costs
- **Symptom**: Google Cloud bill higher than expected
- **Solutions**:
  - Enable query caching
  - Reduce context window size
  - Use Gemini Flash instead of Pro
  - Implement query deduplication
  - Review and optimize queries

## Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use strong, random secrets
   - Rotate JWT secrets regularly

2. **HTTPS Only**
   - Always use SSL certificates
   - Enable HSTS headers
   - Redirect HTTP to HTTPS

3. **Regular Updates**
   - Update dependencies monthly
   - Monitor security advisories
   - Apply patches promptly

4. **Access Control**
   - Use domain restrictions
   - Implement role-based access (future)
   - Monitor authentication logs

5. **Data Protection**
   - Encrypt sensitive data at rest
   - Use secure connection strings
   - Regular security audits

## Support & Resources

- **Documentation**: See README.md and OPTIMIZATION_CHANGELOG.md
- **Issues**: https://github.com/Knoxtes/rag-system/issues
- **Google Cloud**: https://console.cloud.google.com
- **Monitoring**: Check logs/ directory

## Cost Optimization Tips

1. **Use caching aggressively** - Reduces API calls by 80%+
2. **Enable Vertex AI embeddings** - More cost-effective at scale
3. **Optimize context windows** - Smaller contexts = lower costs
4. **Use Gemini Flash** - 10x cheaper than Pro model
5. **Implement query deduplication** - Avoid reprocessing identical queries
6. **Monitor usage** - Set up billing alerts in Google Cloud

## Next Steps

After deployment:
1. ✅ Test authentication flow
2. ✅ Verify all API endpoints
3. ✅ Test with multiple concurrent users
4. ✅ Monitor logs for errors
5. ✅ Set up automated backups
6. ✅ Configure monitoring alerts
7. ✅ Document any custom configurations
8. ✅ Train users on the system

---

**Last Updated**: November 2025  
**Version**: 1.0 - Production Ready
