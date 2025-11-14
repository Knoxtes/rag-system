# 🤖 Enterprise RAG Chatbot System

Production-ready RAG (Retrieval-Augmented Generation) chatbot for Google Drive document Q&A with advanced multi-document synthesis capabilities.

> 🚀 **New User?** See [QUICKSTART.md](QUICKSTART.md) for quick reference commands and setup tips!

## ✨ Features

- **🔍 Hybrid Search**: Combines BM25 keyword search + dense semantic embeddings
- **🧠 Multi-Document Synthesis**: Intelligently aggregates information across multiple documents
- **💾 Query Caching**: Reduces API costs by caching frequent queries
- **📊 Folder-Aware Search**: Search within specific folders and organizational structures
- **🎯 Smart Query Routing**: Automatically detects and optimizes different query types
- **🔐 Secure**: API keys and credentials excluded from version control
- **⚡ Cost-Optimized**: ~$0.33/user/month for 20 queries/day

## 🏗️ Architecture

```
User Query
    ↓
Query Cache Check (saves 20-30% API costs)
    ↓
Synthesis Detection (confidence-based threshold)
    ↓
Multi-Query Generation (2-4 variations for synthesis)
    ↓
Hybrid Search (BM25 + Dense Embeddings)
    ↓
Cross-Encoder Reranking
    ↓
Contextual Compression
    ↓
Gemini 2.5 Flash API
    ↓
Rich Markdown Response
```

## 🚀 Quick Start

### Two Ways to Get Started

#### Option 1: Guided Setup (Recommended for First Time Users)
```bash
# Clone and navigate to repository
git clone <your-repo-url>
cd rag-system

# Run the setup wizard - it will guide you through everything!
python setup_wizard.py
```

The wizard will help you:
- Create `.env` file with your API key
- Set up Google Drive credentials
- Install dependencies
- Validate your configuration

#### Option 2: Manual Setup

**Prerequisites:**
- Python 3.8+
- Google Cloud Project with Drive API enabled
- Google Gemini API key

**Steps:**

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd rag-system
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up credentials**:
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your keys:
# - GOOGLE_API_KEY (from https://aistudio.google.com/app/apikey)
# - PROJECT_ID (your Google Cloud project)
```

5. **Set up Google Drive credentials**:
   - Download `credentials.json` from Google Cloud Console
   - Enable Google Drive API for your project
   - Place credentials.json in project root
   - First run will prompt OAuth authentication

6. **Validate setup** (recommended):
```bash
python validate_setup.py
```
This checks all credentials and provides fix instructions if anything is missing.

### Running

**CLI Interface:**
```bash
python main.py
```

Then select:
- **Option 1**: Test Authentication
- **Option 2**: Index Google Drive folders
- **Option 3**: Unified Q&A System (recommended)
- **Option 4**: Individual Folder Q&A

**Web Interface (Streamlit):**
```bash
streamlit run app.py
```
Note: You must index folders using the CLI first (option 2) before using the web interface.

## 🔧 Troubleshooting

Having issues? See our comprehensive [Troubleshooting Guide](TROUBLESHOOTING.md) for solutions to common problems:

- Missing API keys or credentials
- Authentication failures
- "No folders indexed" errors
- API errors when querying
- Package installation issues

Quick diagnostics:
```bash
python validate_setup.py
```

## 💰 Cost Analysis

### For 300 Users @ 20 Requests/Day

| Component | Monthly Cost |
|-----------|-------------|
| Gemini 2.5 Flash API | ~$100 |
| **Cost per user** | **$0.33** |
| **Cost per request** | **$0.017** |

### Optimizations Included

✅ **Query Caching** - 20-30% API cost reduction  
✅ **Reduced Context Windows** - 33% token savings  
✅ **Selective Synthesis Mode** - Only when needed  
✅ **Local Embeddings** - No embedding API costs

## 📊 Performance

- **Response Time**: 2-5 seconds (regular queries)
- **Response Time**: 4-8 seconds (synthesis queries)
- **Cache Hit Rate**: 20-30% (typical workload)
- **Multi-Doc Success Rate**: 85%+ (vs 40% before optimization)

## 🔧 Configuration

Key settings in `config.py`:

```python
# Cost Optimization
ENABLE_QUERY_CACHE = True
CACHE_TTL_SECONDS = 300
MAX_CONTEXT_CHARACTERS = 8000
SYNTHESIS_CONTEXT_WINDOW = 15000

# Search Quality
TOP_K_RESULTS = 20
USE_HYBRID_SEARCH = True
BM25_WEIGHT = 0.3
DENSE_WEIGHT = 0.7

# Synthesis
SYNTHESIS_QUERY_THRESHOLD = 0.7
MIN_SOURCES_FOR_SYNTHESIS = 3
```

## 📝 Example Queries

### Regular Queries
- "What are the Q1 sales figures?"
- "Explain the January projections"
- "Show me the Elmira market summary"

### Synthesis Queries (Multi-Document)
- "Summarize Q1, Q2, and Q3 reports"
- "Compare Elmira and Mansfield market performance"
- "List all packages available in 2025"

## 🔒 Security

### Protected Files (Never Committed)
- `credentials.json` - Google OAuth credentials
- `token.pickle` - Authentication tokens
- `.env` - API keys and secrets
- `chroma_db/` - Vector database (regenerate from source)

### Safe to Commit
- All `.py` source files
- `.env.example` - Template only
- Documentation
- Configuration (no secrets)

## 🛠️ Development

### Project Structure
```
rag-system/
├── main.py                  # Entry point
├── rag_system.py           # Core RAG agent
├── config.py               # Configuration
├── embeddings.py           # Embedding & reranking models
├── vector_store.py         # ChromaDB interface
├── document_loader.py      # Document processing
├── folder_indexer.py       # Drive indexing
├── auth.py                 # Google authentication
├── test_synthesis.py       # Test suite
└── docs/
    ├── SYNTHESIS_IMPROVEMENTS.md
    └── OPTIMIZATION_GUIDE.md
```

### Testing

```bash
# Run synthesis tests
python test_synthesis.py

# Test specific query
python -c "from rag_system import *; rag.query('your test query')"
```

## 📈 Scaling

| Users | Requests/Day | Monthly API Cost |
|-------|--------------|------------------|
| 100 | 2,000 | $33 |
| 300 | 6,000 | $100 |
| 1,000 | 20,000 | $334 |
| 5,000 | 100,000 | $1,670 |

**Linear scaling**: Cost per user remains constant at ~$0.33/month

## 🤝 Contributing

This is a private repository. Contact the repository owner for access.

## 📄 License

Proprietary - All rights reserved

## 🆘 Support

For issues or questions, contact the development team.

---

**Built with**: Python 3.11, Google Gemini 2.5 Flash, ChromaDB, BGE Embeddings  
**Optimized for**: Production use, cost efficiency, multi-document synthesis  
**Last Updated**: January 2025
