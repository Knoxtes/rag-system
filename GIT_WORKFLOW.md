# Git Workflow Guide
## For Ask.7MountainsMedia.com Deployment

This guide explains how to use Git to deploy and update the RAG system on your Plesk server.

---

## 🚀 Initial Setup (First Time)

### Step 1: Clone Repository

SSH into your Plesk server:

```bash
ssh user@your-server.com
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
```

Clone the repository:

```bash
# Clone the repository (replaces any existing files)
git clone https://github.com/Knoxtes/rag-system.git .

# Or if directory is not empty:
git clone https://github.com/Knoxtes/rag-system.git temp
mv temp/* .
mv temp/.* .
rm -rf temp
```

### Step 2: Run Setup

```bash
chmod +x setup-plesk.sh
./setup-plesk.sh
```

### Step 3: Configure

1. Upload credentials (credentials.json, token.pickle, .env)
2. Configure Plesk Node.js settings
3. Restart application

See [PLESK_ALMALINUX_SETUP.md](PLESK_ALMALINUX_SETUP.md) for complete details.

---

## 🔄 Updating the Application

### Check for Updates

```bash
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com

# Check current status
git status

# Check for remote changes
git fetch origin
git log HEAD..origin/main --oneline
```

### Pull Latest Changes

```bash
# Pull latest code from main branch
git pull origin main
```

If you see merge conflicts, see "Handling Merge Conflicts" section below.

### After Pulling Changes

Depending on what changed:

#### If Backend Changed (Python files)
```bash
# Update Python dependencies
python3 -m pip install --user -r requirements-linux.txt

# Restart application in Plesk
```

#### If Frontend Changed (React app)
```bash
# Rebuild React app
cd chat-app
/opt/plesk/node/22/bin/npm install
/opt/plesk/node/22/bin/npm run build

# Restart application in Plesk
```

#### If Both Changed
```bash
# Update everything
python3 -m pip install --user -r requirements-linux.txt
cd chat-app
/opt/plesk/node/22/bin/npm install
/opt/plesk/node/22/bin/npm run build
cd ..

# Restart application in Plesk
```

---

## 🔧 Common Git Operations

### View Commit History

```bash
# Last 10 commits
git log --oneline -10

# Changes in a specific commit
git show <commit-hash>

# What changed in last pull
git log --oneline HEAD@{1}..HEAD
```

### Check Current Branch

```bash
# Show current branch
git branch

# Show all branches (including remote)
git branch -a
```

### Switch Branches

```bash
# Switch to a different branch
git checkout <branch-name>

# Create and switch to new branch
git checkout -b <new-branch-name>
```

### Discard Local Changes

**Warning**: This will permanently delete your local changes!

```bash
# Discard changes to a specific file
git checkout -- <file-name>

# Discard all local changes
git reset --hard HEAD
```

### View Changes

```bash
# See what files changed
git status

# See actual changes in files
git diff

# See changes in a specific file
git diff <file-name>
```

---

## 🚨 Handling Merge Conflicts

If `git pull` shows merge conflicts:

### Option 1: Keep Remote Version (Recommended)
```bash
# Discard all local changes and use remote version
git reset --hard origin/main
```

### Option 2: Keep Local Changes
```bash
# Stash local changes
git stash

# Pull remote changes
git pull origin main

# Apply stashed changes (may still have conflicts)
git stash pop
```

### Option 3: Manual Resolution
```bash
# Pull changes (will show conflicts)
git pull origin main

# Edit conflicted files (marked with <<<<<<< and >>>>>>>)
# Fix conflicts manually

# After fixing:
git add .
git commit -m "Resolved merge conflicts"
```

---

## 📝 Making Custom Changes

### Local Modifications

If you need to modify files locally:

```bash
# 1. Make your changes
nano config.py

# 2. Check what changed
git status
git diff

# 3. Test your changes
npm start

# 4. Commit changes (optional)
git add .
git commit -m "Custom configuration for production"
```

**Note**: If you don't commit, changes will be preserved but may conflict with future pulls.

### Creating Local Configuration

For environment-specific changes:

1. **Use .env file** (not tracked by git)
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Use .gitignore** to ignore local files
   ```bash
   echo "my-local-config.py" >> .gitignore
   ```

---

## 🔙 Rolling Back

### Rollback to Previous Commit

```bash
# View recent commits
git log --oneline -10

# Rollback to specific commit
git checkout <commit-hash>

# Or rollback to previous version
git checkout HEAD~1

# Rebuild and restart
cd chat-app && npm run build && cd ..
# Restart in Plesk
```

### Return to Latest

```bash
git checkout main
```

---

## 🛠️ Troubleshooting

### Problem: "Your local changes would be overwritten"

**Solution**:
```bash
# Save local changes
git stash

# Pull updates
git pull origin main

# Restore local changes (optional)
git stash pop
```

### Problem: "Permission denied" errors

**Solution**:
```bash
# Check file permissions
ls -la

# Fix ownership (replace user:group with your Plesk user)
chown -R user:group .

# Fix permissions
chmod 755 .
chmod 644 *.md *.txt *.json
chmod 755 *.sh
```

### Problem: "Fatal: not a git repository"

**Solution**:
```bash
# Re-initialize git
rm -rf .git
git init
git remote add origin https://github.com/Knoxtes/rag-system.git
git fetch origin
git checkout -b main origin/main
```

### Problem: Files keep showing as modified

**Solution**:
```bash
# Check what's different
git status
git diff <file-name>

# If it's just line endings:
git config core.autocrlf false

# Reset the file
git checkout HEAD -- <file-name>
```

---

## 📋 Deployment Workflow Checklist

- [ ] SSH into server
- [ ] Navigate to application directory
- [ ] Check for updates: `git fetch origin`
- [ ] Review changes: `git log HEAD..origin/main --oneline`
- [ ] Backup credentials if needed
- [ ] Pull updates: `git pull origin main`
- [ ] Install dependencies if changed
- [ ] Rebuild frontend if changed
- [ ] Restart application in Plesk
- [ ] Verify health: `curl https://Ask.7MountainsMedia.com/api/health`
- [ ] Check logs: `tail -f logs/rag-system.log`
- [ ] Test in browser

---

## 🔐 Security Notes

### Never Commit These Files
- `.env` - Environment configuration
- `credentials.json` - Google Cloud credentials
- `token.pickle` - OAuth tokens
- `chroma_db/` - Vector database (too large)
- `logs/` - Application logs
- `node_modules/` - Node.js dependencies

These are already in `.gitignore` and will not be committed.

### Safe to Commit
- `.env.example` - Template for configuration
- Python source files (*.py)
- React source files (src/)
- Documentation (*.md)
- Configuration files (package.json, requirements.txt)
- Shell scripts (*.sh)

---

## 📚 Additional Resources

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Help**: https://help.github.com
- **Plesk Git Integration**: Check Plesk panel → Git

### Related Documentation
- [PLESK_ALMALINUX_SETUP.md](PLESK_ALMALINUX_SETUP.md) - Complete setup guide
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Deployment verification
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common commands
- [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) - Recent changes

---

## 🎯 Quick Command Reference

```bash
# Update application
git pull origin main

# Check status
git status

# View recent changes
git log --oneline -5

# Discard local changes
git reset --hard HEAD

# Rollback to previous version
git checkout HEAD~1

# Return to latest
git checkout main

# View what changed
git diff

# Check for remote updates
git fetch origin && git log HEAD..origin/main --oneline
```

---

**Last Updated**: November 2025  
**Repository**: https://github.com/Knoxtes/rag-system  
**Target**: Ask.7MountainsMedia.com
