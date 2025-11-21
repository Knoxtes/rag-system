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

- **Python 3.8+** (3.9+ recommended for AlmaLinux 9.7)
- **Node.js 18+** (18.x, 20.x, 22.x, or 25.x supported)
- **npm**

### Development Mode

```bash
# Install dependencies
npm run install:all

# Start unified server (Node.js proxy + Flask backend)
npm start
```

This will simultaneously start:
- **Node.js Proxy** on http://localhost:3000
- **Flask Backend** on http://localhost:5001
- **React Frontend** served via proxy

### Production Build

```bash
# Build React app for production
npm run build

# Start production server
npm start
```

### Individual Scripts

```bash
# Install dependencies separately
npm run install:backend   # Python (requirements-linux.txt)
npm run install:frontend  # Node.js (React app)

# Build only frontend
npm run build:frontend

# Development with hot reload
npm run dev

# Check health
npm run health

# View logs
npm run logs
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

### Optimized for Plesk Obsidian 18.0.73 on AlmaLinux 9.7

**Target Domain**: Ask.7MountainsMedia.com

### Quick Deployment

```bash
# Clone repository
cd /var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com
git clone https://github.com/Knoxtes/rag-system.git .

# Run automated setup
chmod +x setup-plesk.sh
./setup-plesk.sh
```

The script will:
- ✅ Detect Plesk Node.js (22.x, 20.x, or 18.x)
- ✅ Install Python dependencies (requirements-linux.txt)
- ✅ Install Node.js dependencies
- ✅ Build React production app
- ✅ Create required directories
- ✅ Generate secret keys
- ✅ Provide next steps for Plesk configuration

### Manual Plesk Setup

See **[PLESK_ALMALINUX_SETUP.md](PLESK_ALMALINUX_SETUP.md)** for comprehensive step-by-step instructions.

**Key Configuration**:
- **Application Root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com`
- **Document Root**: `/var/www/vhosts/7mountainsmedia.com/Ask.7MountainsMedia.com/chat-app/build`
- **Application Startup File**: `server.js`
- **Node.js Version**: 22.x (recommended) or 20.x
- **Python Dependencies**: `requirements-linux.txt` (clean, Linux-compatible)

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
pip install -r requirements-production.txt
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
- Flask - Web framework
- ChromaDB - Vector database  
- Google API Client - Drive integration
- Sentence Transformers - Embeddings
- And 20+ more (see requirements-production.txt)

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
