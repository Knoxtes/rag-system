# RAG Chat System

A modern, sleek React-based chat interface for your Enhanced RAG System with real-time document search and AI assistance.

## ✨ Features

- 🎨 **Modern Dark Theme**: Sleek, responsive UI with smooth animations
- 🤖 **Real-time AI Chat**: Powered by your enhanced RAG system with quality filtering
- 📚 **Document Previews**: Interactive previews of referenced documents
- 🔄 **Collection Switching**: Easily switch between different document collections
- 📱 **Responsive Design**: Works beautifully on desktop and mobile
- ⚡ **Smooth Animations**: Framer Motion powered transitions and loading states
- 📝 **Markdown Support**: Rich text rendering with syntax highlighting

## 🚀 Quick Start

### Prerequisites

1. **Python Environment**: Make sure your RAG system is set up and working
2. **Node.js**: Install Node.js (v14 or higher) for the React app
3. **Indexed Documents**: Run your folder indexer to have documents available

### Easy Startup (Recommended)

1. **Navigate to your RAG system directory:**
   ```bash
   cd C:\Users\Notxe\Desktop\rag-system
   ```

2. **Run the startup script:**
   ```bash
   python start_chat_system.py
   ```

   This will:
   - Install required dependencies
   - Start the Flask API server (port 5000)
   - Start the React development server (port 3000)
   - Open your browser automatically

3. **Start chatting!** 
   - Go to http://localhost:3000
   - Select a document collection from the sidebar
   - Start asking questions about your documents

### Manual Startup

If you prefer to start services manually:

#### 1. Start the Flask API Server

```bash
# Install Flask dependencies
pip install -r chat-api-requirements.txt

# Start the API server
python chat_api.py
```

#### 2. Start the React App

```bash
# Navigate to the React app directory
cd chat-app

# Install dependencies (first time only)
npm install

# Start the development server
npm start
```

## 📖 Usage

### Basic Chat
1. Type your question in the input field
2. Press Enter or click the send button
3. Watch the AI think and respond with animated typing indicators
4. View referenced documents with clickable previews

### Collection Management
- Use the sidebar to see available document collections
- Click any collection to switch context
- See collection stats (file count, location, etc.)

### Document References
- AI responses include links to source documents
- Hover over document previews to see quick actions
- Click external link icons to open documents in Google Drive

## 🏗️ Architecture

### Backend (Flask API)
- **File**: `chat_api.py`
- **Port**: 5000
- **Purpose**: Interfaces with your existing RAG system
- **Endpoints**:
  - `GET /health` - System health check
  - `GET /collections` - List available collections
  - `POST /chat` - Send chat messages
  - `POST /switch-collection` - Change document collection

### Frontend (React App)
- **Directory**: `chat-app/`
- **Port**: 3000 (development)
- **Tech Stack**: React + TypeScript + Tailwind CSS + Framer Motion
- **Features**: Modern chat UI, animations, markdown rendering

## 🎨 UI Components

### Chat Interface
- **Message Bubbles**: Distinct styling for user vs AI messages
- **Typing Indicators**: Animated dots showing AI is thinking
- **Avatars**: User and Bot icons for easy identification
- **Timestamps**: Message timing information

### Document Previews
- **File Type Icons**: Visual indicators for different document types
- **Metadata**: Shows filename, type, and quick actions
- **Hover Effects**: Smooth transitions and external link buttons
- **Click Actions**: Direct links to Google Drive documents

### Sidebar
- **Collection Switcher**: Easy switching between document sets
- **Connection Status**: Visual indicator of API connectivity
- **Session Stats**: Message count and active collection info

## 🔧 Customization

### Styling
The app uses Tailwind CSS with a custom dark theme. Main colors:
- **Background**: `dark-950` (very dark blue/gray)
- **Surfaces**: `dark-900`, `dark-800` (lighter grays)
- **Accents**: `blue-500` (primary blue), `green-500` (AI indicator)

### Animations
Powered by Framer Motion:
- **Message Animations**: Slide up on appear, fade out on leave
- **Loading States**: Spin and pulse animations
- **Hover Effects**: Scale and color transitions

## 🐛 Troubleshooting

### Common Issues

1. **"Not connected to API server"**
   - Make sure `python chat_api.py` is running
   - Check if port 5000 is available
   - Verify your RAG system dependencies are installed

2. **"Collection not found"**
   - Run your folder indexer first: `python main.py` → option 2
   - Check `indexed_folders.json` exists and has collections

3. **React app won't start**
   - Make sure Node.js is installed
   - Run `npm install` in the `chat-app` directory
   - Check for port 3000 conflicts

4. **API errors in chat**
   - Check Flask server logs for detailed errors
   - Verify your Google Drive authentication is working
   - Ensure your RAG system can initialize properly

### Development Mode

For development, you can run both servers separately:

```bash
# Terminal 1: API Server
python chat_api.py

# Terminal 2: React App
cd chat-app && npm start
```

## 📦 Dependencies

### Python (Flask API)
- `flask` - Web framework
- `flask-cors` - Cross-origin requests
- Your existing RAG system dependencies

### Node.js (React App)
- `react` + `typescript` - Core framework
- `tailwindcss` - Styling framework
- `framer-motion` - Animations
- `react-markdown` - Markdown rendering
- `lucide-react` - Modern icons
- `axios` - HTTP client

## 🚀 Deployment

For production deployment:

1. **Build the React app**: `npm run build` in `chat-app/`
2. **Configure Flask**: Set `debug=False` in `chat_api.py`
3. **Use production server**: Deploy Flask with Gunicorn or similar
4. **Serve static files**: Serve the React build folder with Nginx

## 🤝 Contributing

This chat system is designed to work seamlessly with your existing RAG system. The modular architecture allows for easy extension and customization.

## 📄 License

This project follows the same license as your RAG system.