# 🤖 RAG Chat System

A modern React-based chat interface powered by a RAG (Retrieval-Augmented Generation) system with Google Drive integration.

## ✨ Features

- **Modern React UI**: Dark theme with smooth animations
- **RAG Integration**: AI-powered responses using your documents
- **Google Drive Browser**: Lazy-loading folder navigation  
- **Real-time Chat**: Instant responses with streaming support
- **Multi-Collection Support**: Switch between different document collections
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
- **Flask API** on http://localhost:5000 (backend)
- **React App** on http://localhost:3000 (frontend)

### Manual Installation

If you need to install dependencies separately:

```bash
# Install all dependencies
npm run install:all

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
   pip install -r requirements-production.txt
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
- **RAG System**: Context-aware responses
- **Multi-Collections**: Switch between document sets
- **Vector Search**: Semantic document retrieval
- **OCR Support**: Text extraction from images

### Google Drive
- **Lazy Loading**: Fast folder browsing
- **Search Function**: Find files quickly
- **Shared Drive Support**: Team collaboration
- **Authentication**: Secure OAuth2 flow

---

**Status**: Production Ready ✅  
**Last Updated**: November 2025  
**Version**: 1.0.0
