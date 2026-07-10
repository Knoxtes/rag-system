# RAG Chat System - Plesk Deployment Guide

## Overview

This guide covers deploying the RAG Chat System on Plesk with:
- Python backend (Flask + Passenger)
- React frontend (static build)
- Scheduled document digestion (midnight daily)

## Prerequisites

1. **Plesk with Python Support**
   - Python 3.9+ installed
   - Passenger for Python enabled

2. **Google Cloud Setup**
   - Google Cloud project with Vertex AI enabled
   - Service account key (`service-account-key.json`)
   - OAuth credentials (`credentials.json`)

3. **Domain Configuration**
   - Domain pointed to Plesk server
   - SSL certificate configured

---

## Part 1: Backend Deployment

### Step 1: Upload Files

Upload all backend files to your domain's document root (e.g., `/var/www/vhosts/yourdomain.com/httpdocs/`):

```
httpdocs/
├── passenger_wsgi.py     # Entry point
├── chat_api.py
├── rag_system.py
├── config.py
├── vector_store.py
├── embeddings.py
├── incremental_indexer.py
├── scheduler.py
├── file_tracker.py
├── ... (other .py files)
├── credentials.json      # Google OAuth credentials
├── service-account-key.json  # GCP service account
├── requirements-production.txt
├── .env.production
├── .htaccess
├── static/
│   └── admin-auth.js
├── logs/                 # Create this directory
├── chroma_db/           # Will be created automatically
└── chat-app/
    └── build/           # React build output
```

### Step 2: Configure Environment

1. Copy and configure the environment file:
```bash
cp .env.production.template .env.production
nano .env.production
```

2. Set secure permissions:
```bash
chmod 600 .env.production
chmod 600 credentials.json
chmod 600 service-account-key.json
chmod 600 token.pickle
```

### Step 3: Create Virtual Environment

In Plesk, go to **Domains > yourdomain.com > Python**:

1. Enable Python support
2. Set Python version to 3.9+
3. Set application root to document root
4. Set application startup file to `passenger_wsgi.py`

Or via SSH:
```bash
cd /var/www/vhosts/yourdomain.com/httpdocs
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-production.txt
```

### Step 4: Set Google Cloud Credentials

Add to `.env.production`:
```
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
```

Or in Plesk Python settings, add environment variable:
```
GOOGLE_APPLICATION_CREDENTIALS=/var/www/vhosts/yourdomain.com/httpdocs/service-account-key.json
```

### Step 5: Create Required Directories

```bash
mkdir -p logs
chmod 755 logs
```

### Step 6: Restart Application

In Plesk: **Domains > yourdomain.com > Python > Restart**

---

## Part 2: Frontend Deployment

### Step 1: Build React App

On your development machine:
```bash
cd chat-app
npm install
npm run build
```

### Step 2: Upload Build

Upload the `chat-app/build/` contents to your server. You have two options:

**Option A: Same Domain (Recommended)**
```
httpdocs/
├── passenger_wsgi.py
├── ... (backend files)
└── static/
    ├── css/
    ├── js/
    └── index.html
```

Configure `.htaccess` to serve index.html for frontend routes.

**Option B: Subdomain**
Create separate subdomain (e.g., `app.yourdomain.com`) for the React app.

### Step 3: Configure API URL

In React build, ensure `REACT_APP_API_BASE_URL` points to your backend:
```
# For same domain deployment:
REACT_APP_API_BASE_URL=

# For separate backend:
REACT_APP_API_BASE_URL=https://api.yourdomain.com
```

---

## Part 3: Scheduled Document Digestion

The system includes automatic nightly document indexing that:
- Runs at midnight (configurable)
- Only processes new/changed files
- Removes deleted files from the index
- Saves ~90% on embedding costs vs full re-index

### Option A: Plesk Scheduled Tasks (Recommended)

1. Go to **Tools & Settings > Scheduled Tasks**
2. Add new task for your domain's system user
3. Configure:
   - **Run**: `/usr/bin/python3 /var/www/vhosts/yourdomain.com/httpdocs/scheduler.py --once`
   - **Schedule**: Daily at 00:00

Example cron entry:
```
0 0 * * * cd /var/www/vhosts/yourdomain.com/httpdocs && /usr/bin/python3 scheduler.py --once >> logs/cron.log 2>&1
```

### Option B: Systemd Service (Advanced)

Create `/etc/systemd/system/rag-scheduler.service`:
```ini
[Unit]
Description=RAG Document Scheduler
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/vhosts/yourdomain.com/httpdocs
ExecStart=/usr/bin/python3 scheduler.py --time 00:00
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
systemctl enable rag-scheduler
systemctl start rag-scheduler
```

### Verify Scheduled Sync

Check sync status:
```bash
python3 scheduler.py --status
```

Check logs:
```bash
tail -f logs/scheduler.log
tail -f logs/incremental_indexer.log
```

---

## Part 4: Initial Setup

### Step 1: Authenticate Google Drive

1. Visit: `https://yourdomain.com/admin/dashboard`
2. Login with an admin account
3. Click "Connect Google Drive"
4. Complete OAuth flow

### Step 2: Configure Folders to Index

1. In admin dashboard, select folders to index
2. Run initial index (this may take time)
3. Verify documents are indexed

### Step 3: Run Initial Sync

```bash
cd /var/www/vhosts/yourdomain.com/httpdocs
python3 incremental_indexer.py --sync
```

---

## Part 5: Monitoring & Maintenance

### Health Checks

```bash
# API health
curl https://yourdomain.com/health

# Sync status
python3 scheduler.py --status

# Vector store stats
python3 -c "from vector_store import VectorStore; vs=VectorStore(); print(vs.get_stats())"
```

### Log Files

- `logs/passenger.log` - WSGI server logs
- `logs/rag_system.log` - Application logs
- `logs/scheduler.log` - Scheduled sync logs
- `logs/incremental_indexer.log` - Indexing details

### Common Issues

**1. "Application failed to initialize"**
- Check `logs/passenger.log` for errors
- Verify all dependencies installed
- Check environment variables

**2. "Google Drive authentication failed"**
- Re-run OAuth flow in admin dashboard
- Check `credentials.json` is valid
- Verify redirect URI matches Plesk URL

**3. "Scheduled sync not running"**
- Check Plesk scheduled tasks
- Verify Python path is correct
- Check `logs/cron.log` for errors

**4. "Out of memory"**
- Increase Plesk memory limit
- Reduce `EMBEDDING_BATCH_SIZE` in config

---

## Cost Optimization

The system is optimized for cost-effectiveness:

| Component | Cost | Notes |
|-----------|------|-------|
| Vertex AI Embeddings | ~$0.00002/1K chars | ~$0.30-3/month for 100 users |
| Gemini Flash 2.5 | ~$0.075/1M tokens | Cheapest model, fast |
| Incremental Sync | - | Only processes changed files |
| Embedding Cache | - | Avoids recomputation |
| Query Cache | - | Reduces API calls |

### Tips

1. Use `--dry-run` to preview sync before running
2. Monitor embedding cache hit rate
3. Review `files_skipped` in sync stats (should be high after first sync)
4. Set appropriate `CHUNK_SIZE` to balance quality vs cost

---

## Security Checklist

- [ ] `.env.production` has secure `FLASK_SECRET_KEY`
- [ ] All sensitive files have 600 permissions
- [ ] HTTPS is enabled and working
- [ ] Admin emails are restricted
- [ ] Rate limiting is configured
- [ ] `.htaccess` blocks sensitive files

---

## Support

For issues:
1. Check logs in `logs/` directory
2. Run health check: `curl https://yourdomain.com/health`
3. Test sync manually: `python3 incremental_indexer.py --dry-run`
