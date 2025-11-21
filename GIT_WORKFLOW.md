# Git Workflow for RAG System

This document describes the Git workflow for deploying and maintaining the RAG System on Ask.7MountainsMedia.com.

---

## 🌿 Branch Strategy

### Main Branches

- **`main`** - Production-ready code deployed to Ask.7MountainsMedia.com
- **`develop`** - Development branch for new features and fixes

### Feature Branches

Create feature branches from `develop`:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

---

## 📦 Initial Deployment

### First-Time Setup

```bash
# On your Plesk server
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
git clone https://github.com/Knoxtes/rag-system.git .
git checkout main
```

### Install Dependencies

```bash
bash deploy.sh
```

### Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your production values
```

### Upload Credentials

Upload via SFTP:
- `credentials.json`
- `token.pickle` (if you have it)

### Start Application

Configure and start in Plesk (see QUICK_START.md)

---

## 🔄 Regular Updates

### Updating from Git

When new changes are pushed to the repository:

```bash
# SSH into your server
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com

# Check current status
git status

# Stash any local changes (if needed)
git stash

# Pull latest changes
git pull origin main

# Reinstall dependencies (if needed)
bash deploy.sh

# Or just rebuild frontend
npm run build
```

### After Pulling Changes

Restart the application in Plesk:
1. Go to **Domains** → **Ask.7MountainsMedia.com** → **Node.js**
2. Click **Restart Application**

---

## 🚫 Files Not in Git

The following files are **NOT** tracked by Git (see `.gitignore`):

### Credentials & Secrets
- `credentials.json` - Google Cloud credentials
- `token.pickle` - OAuth tokens
- `.env` - Environment configuration

### Build Artifacts
- `node_modules/` - Node.js dependencies
- `chat-app/build/` - React production build
- `build/`, `dist/` - Build directories

### Database & Logs
- `chroma_db/` - Vector database (520 MB)
- `logs/` - Application logs
- `*.log` - Log files

### Development Files
- `__pycache__/` - Python cache
- `.pytest_cache/` - Test cache
- `package-lock.json` - Auto-generated lock file

**Important:** These files must be managed separately and uploaded via SFTP or created on the server.

---

## 📤 Deploying Changes

### For Developers

#### 1. Make Changes Locally

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# Make your changes
# Test locally
```

#### 2. Commit Changes

```bash
git add .
git commit -m "Add feature: description"
```

#### 3. Push to GitHub

```bash
git push origin feature/my-feature
```

#### 4. Create Pull Request

- Create PR from `feature/my-feature` to `develop`
- After review and approval, merge to `develop`
- Create PR from `develop` to `main` when ready for production

### For Production Deployment

Once changes are merged to `main`:

```bash
# On Plesk server
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
git pull origin main
bash deploy.sh
# Restart in Plesk
```

---

## 🔐 Managing Secrets

### Never Commit These Files

- `credentials.json`
- `token.pickle`
- `.env`
- Any file with API keys or passwords

### How to Update Secrets

1. **Via SFTP:**
   - Connect to server with SFTP client
   - Navigate to project directory
   - Upload updated file

2. **Via Plesk File Manager:**
   - Go to **Files** in Plesk
   - Navigate to project directory
   - Upload file

3. **Via SSH (for .env):**
   ```bash
   cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
   nano .env
   # Make changes
   # Restart application in Plesk
   ```

---

## 🛠️ Common Git Workflows

### Updating Dependencies

When `package.json` or `requirements-production.txt` changes:

```bash
git pull origin main
bash deploy.sh  # Reinstalls everything
```

### Frontend-Only Changes

When only React code changes:

```bash
git pull origin main
cd chat-app
npm install  # If package.json changed
npm run build
cd ..
# Restart in Plesk
```

### Backend-Only Changes

When only Python code changes:

```bash
git pull origin main
python3 -m pip install --user -r requirements-production.txt
# Restart in Plesk
```

### Configuration Changes

When `.env` or environment variables change:

```bash
# Update .env file on server (not in Git)
nano .env

# Or update in Plesk environment variables
# Then restart application
```

---

## 🔍 Checking What Changed

### View Changes Before Pulling

```bash
git fetch origin main
git log HEAD..origin/main --oneline
git diff HEAD..origin/main
```

### View Last Commit

```bash
git log -1
git show HEAD
```

### Check Current Branch and Status

```bash
git branch
git status
git log --oneline -5
```

---

## 🚨 Emergency Rollback

If deployment breaks:

### Option 1: Revert to Previous Commit

```bash
git log --oneline -10  # Find the working commit
git checkout <commit-hash>
bash deploy.sh
# Restart in Plesk
```

### Option 2: Reset to Last Working State

```bash
git fetch origin main
git reset --hard origin/main
bash deploy.sh
# Restart in Plesk
```

### Option 3: Rollback to Specific Tag/Release

```bash
git tag  # List all tags
git checkout v1.0.0  # Replace with actual tag
bash deploy.sh
# Restart in Plesk
```

---

## 📊 Best Practices

### Before Pulling

1. **Check status:** `git status`
2. **Backup database:** Copy `chroma_db/` folder
3. **Note current version:** `git log -1`

### After Pulling

1. **Review changes:** `git log -5`
2. **Check build:** `ls -la chat-app/build/`
3. **Test health endpoint:** `curl localhost:3000/api/health`
4. **Restart application** in Plesk
5. **Verify in browser:** Visit `https://Ask.7MountainsMedia.com`

### Regular Maintenance

- **Weekly:** Check for updates: `git fetch origin main`
- **Monthly:** Review logs: `tail -100 logs/rag_system.log`
- **Quarterly:** Backup `chroma_db/` folder

---

## 🆘 Getting Help

### Check Deployment Logs

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
tail -f logs/rag_system.log
```

### Plesk Logs

Check in Plesk:
- **Domains** → **Ask.7MountainsMedia.com** → **Logs**

### Verify Setup

```bash
bash verify-setup.sh
```

---

## 📖 Related Documentation

- **[QUICK_START.md](QUICK_START.md)** - Fast deployment guide
- **[PLESK_SETUP_GUIDE.md](PLESK_SETUP_GUIDE.md)** - Complete Plesk setup
- **[README.md](README.md)** - Project overview

---

**Repository:** https://github.com/Knoxtes/rag-system  
**Production Domain:** Ask.7MountainsMedia.com  
**Last Updated:** November 2024
