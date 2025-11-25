# 🤖 RAG Chat System
## AI-Powered Document Search & Chat for 7 Mountains Media

A production-ready React + Flask application powered by RAG (Retrieval-Augmented Generation) with Google Drive integration, Vertex AI embeddings, and Document AI OCR.

**Live at**: [Ask.7MountainsMedia.com](https://Ask.7MountainsMedia.com)

---

## ✨ Key Features

### 🎯 AI-Powered Intelligence
- **Advanced RAG System**: Context-aware responses using Vertex AI and ChromaDB
- **Multi-Collection Search**: Query across 11+ document collections simultaneously
- **Smart Routing**: AI-powered query routing to relevant document collections
- **Source Attribution**: Every answer includes source documents and links

### 🚀 Performance Optimizations
- **99.9% Faster Cached Queries**: Sub-50ms response time for repeated questions
- **87% Faster First-Time Queries**: Optimized retrieval pipeline (40s → 5-8s)
- **Multi-Layer Caching**: Redis + semantic similarity + query result caching
- **Lazy Loading**: 90% faster startup (60s → 5s)
- **Response Compression**: 70-80% faster data transfer

### 📁 Google Drive Integration
- **Real-time File Browser**: Browse shared drives with intelligent caching
- **OCR Support**: Extract text from images using Document AI
- **Document Analysis**: Direct file analysis using Gemini's workspace grounding

### 🔐 Enterprise Security
- **Google OAuth 2.0**: Organization-based access control
- **JWT Authentication**: 7-day tokens with auto-refresh
- **Domain Restrictions**: @7mountainsmedia.com only
- **Rate Limiting**: Protect against abuse

## 🚀 Quick Start

### For Production Deployment (Plesk)

**📖 See complete guide**: [PLESK_DEPLOYMENT_GUIDE.md](PLESK_DEPLOYMENT_GUIDE.md)

```bash
# 1. Clone repository
git clone https://github.com/Knoxtes/rag-system.git
cd rag-system

# 2. Run deployment script
chmod +x deploy-plesk.sh
./deploy-plesk.sh

# 3. Configure in Plesk and start
# See PLESK_DEPLOYMENT_GUIDE.md for detailed steps
```

### For Local Development

**Prerequisites**:
- Python 3.9+
- Node.js 22.21.1+
- Google Cloud credentials

```bash
# Install dependencies
pip install -r requirements-production.txt
npm install
cd chat-app && npm install --legacy-peer-deps && cd ..

# Build frontend
cd chat-app && npm run build && cd ..

# Start server
npm start
```

Visit: http://localhost:3000

### System Requirements

- **OS**: Linux (AlmaLinux 9.7 recommended) / macOS / Windows
- **RAM**: 2GB+ recommended
- **Storage**: 1GB+ (excluding vector database)
- **Node.js**: 22.21.1 (or 22.x)
- **Python**: 3.9+

## 📁 Project Structure

```
rag-system/
├── server.js                    # Node.js proxy server (entry point)
├── chat_api.py                  # Flask backend API
├── rag_system.py                # Core RAG system with multi-collection support
├── config.py                    # System configuration
├── auth.py                      # Google Drive authentication
├── oauth_config.py              # OAuth & JWT configuration
├── vector_store.py              # ChromaDB interface
├── vertex_embeddings.py         # Vertex AI embeddings
├── documentai_ocr.py            # Document AI OCR processing
├── package.json                 # Node.js dependencies & scripts
├── requirements-production.txt  # Python dependencies
├── .env.example                 # Environment template
├── deploy-plesk.sh              # Automated deployment script
├── PLESK_DEPLOYMENT_GUIDE.md    # Complete deployment guide
├── chat-app/                    # React frontend
│   ├── src/                     # React source code
│   │   ├── App.tsx              # Main application
│   │   ├── components/          # React components
│   │   └── types/               # TypeScript types
│   ├── build/                   # Production build (generated)
│   ├── package.json             # React dependencies
│   └── install-and-build.sh     # Build script for Node 25.x
├── chroma_db/                   # Vector database (not in git)
├── logs/                        # Application logs (not in git)
└── docs/                        # Additional documentation
```

## 🛠️ Available Scripts

### Production Deployment
- `./deploy-plesk.sh` - Full deployment for Plesk (git pull, dependencies, build)
- `./update-from-git.sh` - Quick update from Git
- `npm run deploy:full` - Update, install dependencies, rebuild frontend
- `npm run deploy:update` - Git pull latest changes

### Development
- `npm start` - Start Node.js proxy + Flask backend
- `npm run dev:frontend` - Start React development server
- `npm run dev:backend` - Start Flask in development mode
- `npm run dev` - Start both with concurrently

### Building
- `npm run build` - Build React app for production
- `npm run build:frontend` - Build using Plesk-optimized script
- `npm run install:deps` - Install all Node.js dependencies
- `npm run install:python` - Install Python dependencies

### Monitoring
- `npm run health` - Check API health status
- `npm run logs` - Tail application logs

## 🌐 Deployment to Plesk

**For complete deployment instructions, see**: [PLESK_DEPLOYMENT_GUIDE.md](PLESK_DEPLOYMENT_GUIDE.md)

### Quick Deployment Steps

1. **Clone & Deploy**
   ```bash
   git clone https://github.com/Knoxtes/rag-system.git
   cd rag-system
   chmod +x deploy-plesk.sh
   ./deploy-plesk.sh
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Generate secret keys: `python3 -c "import secrets; print(secrets.token_hex(32))"`
   - Update domain to: `Ask.7MountainsMedia.com`
   - Upload `credentials.json` and `token.pickle`

3. **Configure Plesk Node.js App**
   - Enable Node.js 22.21.1
   - Set application root and document root
   - Add environment variables
   - Set startup file to `server.js`

4. **Verify Deployment**
   - Visit: https://Ask.7MountainsMedia.com/api/health
   - Should return: `{"status": "healthy"}`

### System Configuration

**Plesk Settings:**
- Node.js Version: 22.21.1
- Application Mode: production
- Application Root: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com`
- Document Root: `/var/www/vhosts/7mountainsmedia.com/Ask.7mountainsmedia.com/chat-app/build`
- Startup File: `server.js`

**Environment Variables** (Set in Plesk):
- `FLASK_ENV=production`
- `NODE_ENV=production`
- `PORT=3000`
- `FLASK_PORT=5001`
- Plus all OAuth and Google Cloud credentials

## 🔧 Configuration

### Required Files

1. **credentials.json** - Google Cloud Service Account
   - Enable: Vertex AI, Document AI, Drive API
   - Download from Google Cloud Console

2. **token.pickle** - OAuth token (auto-generated on first login)

3. **.env** - Environment configuration
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

### Key Environment Variables

```env
# Security (Generate unique values!)
FLASK_SECRET_KEY=<generate-with-secrets-module>
JWT_SECRET_KEY=<generate-with-secrets-module>

# OAuth
OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback
ALLOWED_DOMAINS=7mountainsmedia.com

# Google Cloud
PROJECT_ID=rag-chatbot-475316
GOOGLE_API_KEY=<your-api-key>

# Production settings
FLASK_ENV=production
DEBUG=False
CORS_ORIGINS=https://Ask.7MountainsMedia.com
```

### Google Cloud Setup

1. **Create Project** at console.cloud.google.com
2. **Enable APIs**:
   - Vertex AI API
   - Document AI API
   - Google Drive API
3. **Create Service Account** and download credentials
4. **Configure OAuth 2.0**:
   - Create OAuth Client ID
   - Add authorized redirect URI
   - Download client secrets

## 🎯 API Endpoints

### Health & Status
- `GET /api/health` - Health check with backend status
- `GET /api/stats` - System statistics and cache performance

### Authentication
- `GET /auth/login` - Initiate Google OAuth flow
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/status` - Check authentication status
- `POST /auth/logout` - Logout and clear session

### Chat & RAG
- `POST /chat` - Send chat messages (requires JWT)
- `GET /collections` - List available document collections
- `POST /switch-collection` - Switch active collection

### Google Drive
- `GET /folders` - Browse Drive folders (lazy loading)
- `GET /folders/search` - Search files and folders
- `POST /folders/batch` - Batch load multiple folders
- `GET /drive/file/:id` - Get specific file metadata

### Admin (Requires admin role)
- `POST /admin/reindex` - Trigger reindexing
- `GET /admin/cache/status` - Detailed cache statistics
- `POST /admin/cache/clear` - Clear all caches

## 🐛 Troubleshooting

### Application Won't Start (502 Bad Gateway)

**Check processes:**
```bash
ps aux | grep -E "node|python.*chat_api"
```

**Check logs:**
```bash
tail -f logs/rag_system.log
tail -f logs/chat_api.log
```

**Solution**: Restart in Plesk → Node.js → Restart App

### OAuth Redirect Fails

**Error**: "redirect_uri_mismatch"

**Solutions:**
1. Verify `.env`: `OAUTH_REDIRECT_URI=https://Ask.7MountainsMedia.com/auth/callback`
2. Check Google Cloud Console: Authorized redirect URIs must match exactly
3. Must use HTTPS, no trailing slash

### React Build Fails

**Error**: localStorage or Node.js compatibility issues

**Solution:**
```bash
cd chat-app
rm -rf node_modules build
npm install --legacy-peer-deps
./install-and-build.sh
```

### Module Import Errors

**Error**: `ModuleNotFoundError`

**Solution:**
```bash
pip install --upgrade -r requirements-production.txt
# Restart application in Plesk
```

### Flask Backend Not Responding

**Check Flask port:**
```bash
netstat -tulpn | grep 5001
```

**Verify credentials:**
```bash
ls -la credentials.json token.pickle
```

**Restart Flask** (Plesk auto-restarts when you restart the Node.js app)

For more troubleshooting, see [PLESK_DEPLOYMENT_GUIDE.md](PLESK_DEPLOYMENT_GUIDE.md#troubleshooting)

## 📊 Performance Metrics

### Response Times
- **First-time query**: 5-8 seconds (RAG retrieval + LLM)
- **Cached query**: <50ms (99.9% faster)
- **Similar query (semantic cache)**: <200ms (99.5% faster)

### Resource Usage
- **Memory**: 200-300MB typical
- **CPU**: <5% idle, 20-50% under load
- **Storage**: ~1GB (excluding chroma_db)

### Active Optimizations (11 total)
✅ Connection Pooling (50% faster DB)
✅ Parallel Search (60-70% faster)
✅ Redis Cache (persistent)
✅ Semantic Cache (30-40% more hits)
✅ Lazy Loading (90% faster startup)
✅ Response Compression (99% size reduction)
✅ SSE Streaming (<1s latency)
✅ HNSW Optimization (20-30% faster)
✅ Fast Keyword Routing (<1ms)
✅ Query Result Caching
✅ Reduced Search Scope

---

## 📚 Technology Stack

### Backend
- **Flask 3.1.0** - Web framework
- **ChromaDB 1.2.1** - Vector database
- **Sentence Transformers 3.3.1** - Embeddings
- **Google Cloud Vertex AI** - LLM & embeddings
- **Google Document AI** - OCR processing
- **PyJWT 2.8.0** - Authentication
- **Redis** - Persistent caching

### Frontend
- **React 19** - UI framework
- **TypeScript 4.9** - Type safety
- **Tailwind CSS 3.4** - Styling
- **Framer Motion 12** - Animations
- **Axios** - API client
- **React Markdown** - Rich text rendering

### Infrastructure
- **Node.js 22.21.1** - Proxy server
- **Express 4.18** - Node.js framework
- **Plesk Obsidian 18.0.73** - Hosting platform
- **AlmaLinux 9.7** - Operating system

---

## 📖 Documentation

- **[PLESK_DEPLOYMENT_GUIDE.md](PLESK_DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[.env.example](.env.example)** - Environment configuration template
- **[VERTEX_AI_MIGRATION.md](VERTEX_AI_MIGRATION.md)** - Vertex AI setup
- **[DOCUMENTAI_SETUP.md](DOCUMENTAI_SETUP.md)** - OCR configuration

---

## 🔗 Links

- **Live Site**: https://Ask.7MountainsMedia.com
- **Repository**: https://github.com/Knoxtes/rag-system
- **Branch**: feature/easyocr-integration
- **Organization**: 7 Mountains Media

---

## 📝 License

MIT License - Copyright (c) 2025 7 Mountains Media

---

## 🆘 Support

For deployment issues or questions:
1. Check [PLESK_DEPLOYMENT_GUIDE.md](PLESK_DEPLOYMENT_GUIDE.md)
2. Review [Troubleshooting](#troubleshooting) section
3. Check application logs: `tail -f logs/rag_system.log`
4. Verify configuration in `.env` file

---

**Status**: ✅ Production Ready  
**Version**: 2.0.0  
**Last Updated**: November 21, 2025  
**Deployed On**: Plesk Obsidian 18.0.74 | AlmaLinux 9.7 | Node.js 22.21.1
