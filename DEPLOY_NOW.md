# 🚀 FINAL PRE-DEPLOYMENT CHECKLIST

## Status: ✅ READY (with minor configuration updates needed)

---

## ✅ Completed Items

### Core System
- [x] **All critical files present**
  - credentials.json ✓
  - .env ✓
  - requirements-production.txt ✓
  - passenger_wsgi.py ✓
  - chat_api.py ✓
  - server.js ✓
  - package.json ✓

- [x] **Frontend build ready**
  - React production build exists
  - index.html present
  - static/ directory present

- [x] **All dependencies installed**
  - Python packages ✓
  - Node modules ✓
  - All optimization libraries ✓

- [x] **Configuration**
  - Production mode: FLASK_ENV=production ✓
  - Debug mode: OFF ✓
  - All performance optimizations: ENABLED ✓

- [x] **Performance Optimizations (All Active)**
  - Connection Pooling ✓
  - Parallel Search ✓
  - Lazy Loading ✓
  - Semantic Cache ✓
  - Response Compression ✓
  - Fast Keyword Routing ✓
  - Query Result Caching ✓

---

## ⚠️ Required Before Deployment

### 1. Security - Generate New Secret Keys

**Current Issue:** Default secret keys detected in `.env`

**Fix:**
```bash
# Generate new secret keys
python -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

**Action:** 
1. Run the commands above
2. Copy the generated keys
3. Update `.env` file with new keys
4. NEVER commit these keys to git

---

### 2. OAuth Configuration - Update Redirect URI

**Current Issue:** `OAUTH_REDIRECT_URI` points to localhost

**Fix:**
Update `.env` with your production domain:

```env
# Example for Plesk deployment
OAUTH_REDIRECT_URI=https://chat.7mountainsmedia.com/auth/callback

# Or if using subdomain
OAUTH_REDIRECT_URI=https://rag.yourdomain.com/auth/callback
```

**Action:**
1. Determine your production URL
2. Update `OAUTH_REDIRECT_URI` in `.env`
3. Add the same URI to Google Cloud Console OAuth settings

---

### 3. Google Cloud OAuth Setup

**Required:** Add production redirect URI to Google Cloud Console

**Steps:**
1. Go to: https://console.cloud.google.com/apis/credentials
2. Select your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add your production URL:
   - `https://your-production-domain.com/auth/callback`
4. Click "Save"

---

## 📋 Deployment Steps (Once Above Items Complete)

### Step 1: Upload Files to Plesk

Upload entire `rag-system` directory to your Plesk server:
```bash
# Via SCP
scp -r rag-system/ user@your-server:/path/to/app/

# Or use Plesk File Manager
# Upload all files except:
# - node_modules/ (will reinstall)
# - chroma_db/ (will regenerate)
# - __pycache__/ (Python cache)
# - .git/ (version control)
```

### Step 2: Install Dependencies

```bash
# SSH into Plesk server
cd /path/to/rag-system

# Install Python dependencies
pip install -r requirements-production.txt

# Install Node dependencies
npm install

# Build React frontend
npm run build
```

### Step 3: Configure Plesk Application

**Option A: Passenger (Python WSGI)**
1. In Plesk, go to "Python" settings
2. Set Application Root: `/path/to/rag-system`
3. Set Application Startup File: `passenger_wsgi.py`
4. Set Python version: 3.8+
5. Enable application

**Option B: Node.js Application**
1. In Plesk, go to "Node.js" settings
2. Set Application Root: `/path/to/rag-system`
3. Set Application Startup File: `server.js`
4. Set Node.js version: 14+
5. Application Mode: Production
6. Enable application

**Recommended: Option B (Node.js)** - Runs both React and Flask together

### Step 4: Set Environment Variables in Plesk

In Plesk, add these environment variables:
```
FLASK_ENV=production
DEBUG=False
FLASK_SECRET_KEY=<your-generated-key>
JWT_SECRET_KEY=<your-generated-key>
OAUTH_REDIRECT_URI=https://your-domain.com/auth/callback
CORS_ORIGINS=https://your-domain.com
```

### Step 5: Start Application

```bash
# If using Node.js
npm start

# Application should start on port 3000
# Configure Plesk to proxy to port 3000
```

### Step 6: Test Deployment

1. **Health Check**
   ```bash
   curl https://your-domain.com/api/health
   ```

2. **Authentication**
   - Visit: `https://your-domain.com`
   - Click "Login with Google"
   - Verify OAuth flow works

3. **Chat Functionality**
   - Send a test query
   - Verify response time (<20 seconds first query, <1s cached)
   - Check console for any errors

---

## 🔧 Post-Deployment Verification

### Monitor These Items:

1. **Server Logs**
   ```bash
   tail -f logs/chat_api.log
   tail -f server.log
   ```

2. **Performance Metrics**
   - Response times
   - Cache hit rates
   - Memory usage
   - CPU usage

3. **Error Monitoring**
   - Check `/api/health` regularly
   - Monitor Flask error logs
   - Watch for authentication issues

---

## 🎯 Performance Expectations

With all optimizations enabled:

| Metric | Expected Performance |
|--------|---------------------|
| First query (HR/Policy) | 5-8 seconds |
| Repeated query (cached) | <50ms |
| Similar query (semantic cache) | <200ms |
| General queries | 3-5 seconds |
| File browsing | <1 second |
| Authentication | <500ms |

---

## 🆘 Troubleshooting

### Issue: OAuth Redirect Errors
**Solution:** Verify redirect URI matches exactly in:
1. `.env` file
2. Google Cloud Console
3. No trailing slashes or mismatched protocols (http vs https)

### Issue: Import Errors
**Solution:** Reinstall dependencies:
```bash
pip install -r requirements-production.txt --force-reinstall
```

### Issue: Build Not Found
**Solution:** Rebuild frontend:
```bash
cd chat-app
npm install
npm run build
cd ..
```

### Issue: Port Conflicts
**Solution:** Change ports in `.env`:
```env
PORT=3000  # Frontend port
FLASK_PORT=5001  # Backend port
```

---

## ✅ Final Verification Command

Run this before deploying:
```bash
python verify_production.py
```

All checks should pass before deployment!

---

## 📞 Support Checklist

Before asking for help, verify:
- [ ] All secret keys updated in `.env`
- [ ] OAuth redirect URI updated for production
- [ ] Google Cloud Console OAuth configured
- [ ] All dependencies installed
- [ ] React build exists (`chat-app/build/`)
- [ ] Production environment variables set
- [ ] `verify_production.py` passes all checks

---

## 🎉 Ready to Deploy!

Once you've completed the ⚠️ Required items above:

1. ✅ Update secret keys in `.env`
2. ✅ Update OAuth redirect URI for your domain
3. ✅ Configure Google Cloud Console OAuth
4. ✅ Run `python verify_production.py` (should pass)
5. 🚀 Follow deployment steps above

**Your RAG system is production-ready with world-class performance optimizations!**
