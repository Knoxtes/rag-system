# 🤖 RAG Chat System

A modern React-based chat interface powered by a RAG (Retrieval-Augmented Generation) system with Google Drive integration.

## ✨ Features

- **Modern React UI**: Dark theme with smooth animations
- **RAG Integration**: AI-powered responses using your documents
- **Multi-Collection Support**: Switch between different document collections or search all collections simultaneously  
- **All Collections Mode**: NEW unified search across all indexed collections with smart result synthesis
- **Google Drive Browser**: High-speed lazy-loading with intelligent caching
- **Real-time Chat**: Instant responses with streaming support
- **Multi-Collection Support**: Switch between different document collections
- **Performance Optimized**: Multi-layer caching, compression, and concurrent requests
- **Production Ready**: Optimized for deployment on Plesk and other hosting platforms

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+** 
- **npm**

### One-Command Start

```bash
npm start
```

This will simultaneously start:
- **Flask API** on http://localhost:3000 (unified server)
- **React App** on http://localhost:3000 (frontend)

### Manual Installation

If you need to install dependencies separately:

```bash
# Install all dependencies (recommended - production-ready)
pip install -r requirements-unified.txt

# Or install individually
npm run install:backend  # Python dependencies
npm run install:frontend # Node.js dependencies
```

## 📁 Project Structure

```
rag-system/
├── chat_api.py                  # Flask API server
├── rag_system.py               # Core RAG functionality  
├── auth.py                     # Google authentication
├── package.json                # Root npm config (unified start)
├── passenger_wsgi.py           # WSGI entry point for Plesk
├── requirements-production.txt # Python dependencies
├── chat-app/                   # React frontend
│   ├── src/App.tsx            # Main chat interface
│   ├── package.json           # React dependencies
│   └── build/                 # Production build (after npm run build)
└── chroma_db/                 # Vector database
```

## 🛠️ Available Scripts

### Development
- `npm start` - Start both backend and frontend simultaneously
- `npm run dev` - Same as start (alias)
- `npm run start:backend` - Start only Flask API
- `npm run start:frontend` - Start only React app

### Production
- `npm run build` - Build React app for production
- `npm run production` - Start Flask API in production mode

### Installation  
- `npm run install:all` - Install all dependencies
- `npm run install:backend` - Install Python dependencies
- `npm run install:frontend` - Install Node.js dependencies

## 🌐 Deployment to Plesk

### Automatic Deployment

Run the deployment script:

```bash
# Windows
deploy.bat

# Linux/Mac  
bash deploy.sh
```

### Manual Plesk Setup

1. **Upload Files**: Upload entire project to your domain directory

2. **Python App Configuration**:
   - Entry point: `passenger_wsgi.py`
   - Python version: 3.8+ 

3. **Static Files**:
   - Static files directory: `chat-app/build/`
   - Static files URL: `/`

4. **Environment Variables** (in Plesk):
   ```
   FLASK_ENV=production
   PYTHONPATH=/path/to/your/app
   ```

5. **Build Frontend**:
   ```bash
   cd chat-app && npm run build
   ```

6. **Install Dependencies**:
   ```bash
   pip install -r requirements-unified.txt
   ```

7. **Restart Application** in Plesk control panel

## 🔧 Configuration

### Google Drive Setup

1. Create credentials in Google Cloud Console
2. Download `credentials.json`
3. Place in root directory
4. Run authentication flow on first start

### Environment Variables

Create `.env` file (optional):
```env
FLASK_ENV=development
FLASK_DEBUG=true
GOOGLE_DRIVE_FOLDER_ID=your_shared_drive_id
```

## 🎯 API Endpoints

- `GET /health` - Health check
- `POST /chat` - Send chat messages
- `GET /collections` - List available collections
- `POST /switch-collection` - Switch document collections
- `GET /folders` - Browse Google Drive folders (lazy loading)
- `GET /folders/search` - Search folders and files
- `GET /cache/status` - View cache performance statistics
- `POST /cache/clear` - Clear all cached data
- `POST /cache/preload` - Manually trigger cache preloading
- `POST /folders/batch` - Load multiple folders simultaneously for better performance

## 🐛 Troubleshooting

### Port Conflicts
If port 5000 or 3000 is in use:
```bash
npm run start:backend -- --port 5001
npm run start:frontend  # React will auto-detect available port
```

### Python Dependencies
If imports fail:
```bash
pip install -r requirements-unified.txt
```

### React Build Issues
Clear cache and rebuild:
```bash
cd chat-app
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📋 Dependencies

### Backend (Python)
See `requirements-unified.txt` for complete list:
- Flask - Web framework
- ChromaDB - Vector database  
- Google API Client - Drive integration
- Sentence Transformers - Embeddings
- LangChain - AI orchestration
- And 100+ production-ready dependencies

For detailed installation, see `MULTI_USER_DEPLOYMENT.md`

### Frontend (React/TypeScript)
- React 19 - UI framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Framer Motion - Animations
- Axios - API client
- React Markdown - Message rendering

## 🎨 Features

### Chat Interface
- **Dark Theme**: Professional dark UI
- **Smooth Animations**: Framer Motion powered
- **Markdown Support**: Rich text formatting
- **Responsive Design**: Works on all devices

### Document Integration  
- **Advanced RAG System**: Context-aware responses with agent-based reasoning
- **Multi-Collection Support**: Switch between individual document collections or search all simultaneously
- **All Collections Mode**: Unified search across all indexed collections with intelligent result synthesis
- **Cross-Collection Ranking**: Smart re-ranking ensures best results regardless of source collection
- **Source Attribution**: Always shows which collection provided each piece of information
- **Vector Search**: Semantic document retrieval with hybrid BM25 + dense search
- **OCR Support**: Text extraction from images and documents

### Google Drive
- **Ultra-Fast Caching**: Advanced multi-layer cache system with 6-hour expiry and memory promotion
- **Smart Prefetching**: Automatically preloads top 8 most-accessed folders with deeper structure  
- **Batch Loading**: Load multiple folders simultaneously to reduce API calls
- **Intelligent Preloading**: Background concurrent folder structure caching with performance timing
- **Progressive Rendering**: Stream results as they load with instant expansion for prefetched content
- **Visual Performance Indicators**: ⚡ lightning bolts show prefetched folders, loading spinners for active requests
- **Memory Optimization**: Frequently accessed items cached in memory with LRU eviction
- **SSL Retry Logic**: Robust error handling with exponential backoff (1s, 2s, 4s delays)
- **Search Function**: Find files quickly with client-side result caching and 300ms debouncing
- **Shared Drive Support**: Enterprise-grade performance for team collaboration
- **Authentication**: Secure OAuth2 flow with persistent token management

---

**Status**: Production Ready ✅  
**Last Updated**: November 2025  
**Version**: 1.0.0

## 🚀 Production Ready Features

### Multi-User Support
✅ **Concurrent users**: Thread-safe operations with session isolation  
✅ **Authentication**: OAuth 2.0 with JWT tokens  
✅ **Rate limiting**: 200 requests/day, 50 requests/hour per IP  
✅ **Security headers**: HSTS, XSS protection, frame denial  
✅ **Domain restrictions**: Configurable email domain whitelist  

### Performance & Scalability
✅ **Multi-layer caching**: Folder, embedding, and query caching  
✅ **Background tasks**: Non-blocking cache refresh  
✅ **Batch operations**: Efficient bulk data loading  
✅ **Resource optimization**: Memory management and LRU eviction  
✅ **Connection pooling**: Efficient API connection management  

### Monitoring & Maintenance
✅ **Health checks**: `/health` endpoint for uptime monitoring  
✅ **Structured logging**: Production-grade logging with rotation  
✅ **Error tracking**: Comprehensive exception handling  
✅ **Cost monitoring**: Built-in API cost tracking  

### Documentation
📖 **Full deployment guide**: See `MULTI_USER_DEPLOYMENT.md`  
📖 **Optimization log**: See `OPTIMIZATION_CHANGELOG.md`  
📖 **Configuration reference**: See `config.py`  

For production deployment instructions, see **[Multi-User Deployment Guide](MULTI_USER_DEPLOYMENT.md)**
