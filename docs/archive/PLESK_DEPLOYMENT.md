# RAG System - Plesk Deployment Guide

## 🚀 Quick Start for Plesk

This RAG (Retrieval-Augmented Generation) system is now optimized for single-command deployment on Plesk servers.

### Prerequisites

- **Node.js** 14+ (for proxy server and React frontend)
- **Python** 3.8+ (for Flask backend and AI processing)
- **Google Cloud credentials** (for Google Drive integration and Gemini AI)

### 🎯 One-Command Deployment

```bash
npm start
```

That's it! This command will:
1. Start the Flask backend on port 5000
2. Start the Node.js proxy server on port 3000
3. Serve the React frontend through the proxy
4. Handle all API routing automatically

### 📋 Full Setup Process

1. **Clone and Enter Directory**
   ```bash
   git clone <your-repo>
   cd rag-system
   ```

2. **Run Deployment Script**
   ```bash
   # On Linux/Mac
   ./deploy.sh
   
   # On Windows
   deploy.bat
   ```

3. **Start the System**
   ```bash
   npm start
   ```

### 🔧 Environment Configuration

Create these files with your credentials:

#### `credentials.json` (Google Cloud Service Account)
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "...",
  "client_x509_cert_url": "..."
}
```

#### Environment Variables (optional)
```bash
export FLASK_ENV=production
export NODE_ENV=production
export PORT=3000  # Default proxy port
export FLASK_PORT=5000  # Default Flask port
```

### 🏗️ System Architecture

```
User Request → Node.js Proxy (Port 3000) → Flask Backend (Port 5000)
                     ↓
              React Frontend (Static Files)
```

- **Node.js Proxy**: Handles routing, serves React build, proxies API calls
- **Flask Backend**: RAG system, Google Drive integration, AI processing
- **React Frontend**: Chat interface, file browser, workspace analysis

### 🔑 Key Features

1. **Intelligent RAG System**: Context-aware responses using ChromaDB
2. **Google Drive Integration**: Direct document access and analysis
3. **Workspace Analysis**: Document-specific queries with Gemini AI
4. **Extended Authentication**: 7-day JWT tokens with 30-day refresh
5. **Auto-Recovery**: Automatic Google Drive reconnection
6. **Production Ready**: Optimized for Plesk hosting environments

### 📁 Project Structure

```
rag-system/
├── server.js              # Node.js proxy server
├── package.json           # Unified npm scripts
├── chat_api.py            # Main Flask application
├── oauth_config.py        # Authentication system
├── rag_system.py          # RAG processing
├── vector_store.py        # ChromaDB integration
├── credentials.json       # Google Cloud credentials
├── chat-app/              # React frontend
│   ├── src/
│   ├── build/             # Production build
│   └── package.json
├── chroma_db/             # Vector database
└── logs/                  # System logs
```

### 🛡️ Security Features

- JWT token authentication with automatic refresh
- Google OAuth integration
- Secure credential management
- CORS protection
- Rate limiting ready

### 📊 Monitoring

- Health monitoring endpoint: `/api/health`
- System stats: `/api/stats`
- Error logging in `logs/` directory
- Real-time chat logging

### 🔄 Development vs Production

#### Development Mode
```bash
npm run dev
```
- Hot reloading
- Debug logging
- Development React server

#### Production Mode
```bash
npm start
```
- Optimized React build
- Production logging
- Single server process

### 🚨 Troubleshooting

#### Common Issues

1. **Port Conflicts**
   - Default ports: 3000 (proxy), 5000 (Flask)
   - Change in `server.js` and restart

2. **Google Drive Authentication**
   - Check `credentials.json` placement
   - Verify Google Cloud API enablement
   - Check service account permissions

3. **React Build Issues**
   - Run `npm run build` manually
   - Check for TypeScript/ESLint errors
   - Verify `chat-app/build/` exists

4. **Python Dependencies**
   - Install: `pip install -r requirements.txt`
   - Check Python version compatibility

#### Debug Commands

```bash
# Check system status
npm run health

# View logs
tail -f logs/chat_api.log

# Restart with verbose logging
DEBUG=* npm start
```

### 📈 Performance Optimization

- React production build with code splitting
- ChromaDB vector caching
- Google Drive API response caching
- Efficient embedding generation
- Optimized file chunking

### 🔄 Updates and Maintenance

1. **Update Dependencies**
   ```bash
   npm update
   pip install -r requirements.txt --upgrade
   ```

2. **Rebuild Frontend**
   ```bash
   npm run build
   ```

3. **Clear Vector Cache**
   ```bash
   rm -rf chroma_db/
   # System will rebuild on next use
   ```

### 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in `logs/` directory
3. Verify all prerequisites are installed
4. Ensure Google Cloud credentials are properly configured

---

**Ready for production deployment on Plesk servers! 🎉**