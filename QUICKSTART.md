# Quick Reference

## 🚀 Getting Started

### First Time Setup
```bash
# Run the setup wizard (recommended)
python setup_wizard.py

# Or manually:
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
python validate_setup.py
pip install -r requirements.txt
```

### Start Using
```bash
# CLI Interface
python main.py

# Web Interface (Streamlit)
streamlit run app.py
```

---

## 📋 Common Commands

### Check Setup
```bash
python validate_setup.py
```

### Test Authentication
```bash
python auth.py
# or
python main.py  # Select option 1
```

### Index Google Drive Folders
```bash
python main.py  # Select option 2
```

### Query Documents (CLI)
```bash
python main.py  # Select option 3 (recommended) or 4
```

### Query Documents (Web UI)
```bash
streamlit run app.py
```

---

## 🔧 Troubleshooting

### Quick Fixes

| Problem | Solution |
|---------|----------|
| Missing API key | Add `GOOGLE_API_KEY` to `.env` file |
| Authentication fails | Download `credentials.json` from Google Cloud Console |
| "No folders indexed" | Run `python main.py`, select option 2 |
| Import errors | Run `pip install -r requirements.txt` |
| Token errors | Delete `token.pickle` and re-authenticate |

### Get Detailed Help
```bash
# See full troubleshooting guide
cat TROUBLESHOOTING.md

# Or view in browser (if available)
python -m markdown TROUBLESHOOTING.md > troubleshooting.html
```

---

## 📁 Important Files

| File | Purpose | Required? |
|------|---------|-----------|
| `.env` | API keys and configuration | ✅ Yes |
| `credentials.json` | Google OAuth credentials | ✅ Yes |
| `token.pickle` | Authentication token | Auto-generated |
| `indexed_folders.json` | Index log | Auto-generated |
| `chroma_db/` | Vector database | Auto-generated |

---

## 🔑 Getting API Keys & Credentials

### 1. Google Gemini API Key
1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API key"
3. Copy and add to `.env` file

### 2. Google Drive Credentials
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Desktop app)
3. Download JSON as `credentials.json`
4. Enable Google Drive API for your project

---

## 💡 Tips

- **First time?** Run `python setup_wizard.py` for guided setup
- **Having issues?** Run `python validate_setup.py` to diagnose
- **Need help?** Check `TROUBLESHOOTING.md` for detailed solutions
- **Index first!** You must index folders (option 2) before querying

---

## 📊 Menu Options Explained

### CLI Menu (`python main.py`)

| Option | What it does |
|--------|-------------|
| 1 | Test your Google Drive authentication |
| 2 | Index folders from Google Drive (required first step!) |
| 3 | Unified Q&A - Smart search across all indexed folders |
| 4 | Individual Folder Q&A - Query a specific folder |
| 5 | Check system status and configuration |
| 6 | Clear all indexed data and start fresh |
| 7 | Exit |

---

## 🌐 Web Interface Features

The Streamlit web interface (`streamlit run app.py`) provides:
- Beautiful, user-friendly chat interface
- Automatic agent selection
- Real-time responses with citations
- Chat history
- Markdown rendering for rich responses

**Note:** You must index folders using the CLI first (option 2) before the web interface will work.

---

## 🐛 Debug Mode

For more detailed error messages:

```bash
# Streamlit debug mode
streamlit run app.py --logger.level=debug

# Python debug mode
python -u main.py
```

---

## 🔄 Updating

```bash
# Pull latest changes
git pull

# Update dependencies (if requirements changed)
pip install -r requirements.txt --upgrade

# Validate setup after update
python validate_setup.py
```

---

## 📞 Support

- **Validation Issues:** Run `python validate_setup.py`
- **Common Problems:** See `TROUBLESHOOTING.md`
- **Documentation:** See `README.md`
- **Setup Help:** Run `python setup_wizard.py`

---

*Last Updated: November 2024*
