# 🔧 Troubleshooting Guide

This guide helps you resolve common issues with the RAG System.

## Quick Diagnostics

Run the validation script to check your setup:
```bash
python validate_setup.py
```

This will check all required configurations and provide specific fix instructions.

---

## Common Issues

### 1. "GOOGLE_API_KEY is not set"

**Symptom:** Application fails to start with error about missing API key.

**Cause:** The Google Gemini API key is not configured.

**Fix:**
1. Get your API key from: https://aistudio.google.com/app/apikey
2. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your key:
   ```
   GOOGLE_API_KEY=your_actual_key_here
   ```
4. Restart the application

**Alternative:** Set as environment variable:
```bash
# Linux/Mac
export GOOGLE_API_KEY=your_key_here

# Windows
set GOOGLE_API_KEY=your_key_here
```

---

### 2. "credentials.json not found"

**Symptom:** Application fails with "GOOGLE DRIVE AUTHENTICATION ERROR" and mentions missing credentials.json.

**Cause:** Google Drive OAuth credentials are not configured.

**Fix:**
1. Go to [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing one
3. Enable **Google Drive API** for your project:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"
4. Create OAuth 2.0 Client ID credentials:
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: **Desktop app**
   - Name: RAG System (or any name)
   - Click "Create"
5. Download the credentials JSON file
6. Save it as `credentials.json` in the project root directory
7. Restart the application

---

### 3. "Failed to authenticate" or OAuth errors

**Symptom:** Browser opens but authentication fails, or you get OAuth errors.

**Common Causes & Fixes:**

#### A. OAuth Consent Screen Not Configured
1. Go to [Google Cloud Console - OAuth Consent](https://console.cloud.google.com/apis/credentials/consent)
2. Configure the OAuth consent screen:
   - User Type: External (unless you have Google Workspace)
   - Fill in required fields (App name, User support email, Developer contact)
   - Add scopes: `https://www.googleapis.com/auth/drive.readonly`
   - Add your email as a test user
3. Save and try again

#### B. Redirect URI Mismatch
- Delete `token.pickle` if it exists
- Run authentication again
- Make sure you allow the browser popup

#### C. Port Already in Use
- The authentication uses a random local port
- If you get port errors, close other applications that might be using ports
- Try again

---

### 4. "No folders have been indexed yet"

**Symptom:** Streamlit app shows warning that no folders are indexed.

**Cause:** You need to index Google Drive folders before querying.

**Fix:**
1. Stop the Streamlit app
2. Run the CLI:
   ```bash
   python main.py
   ```
3. Select option 2: "Index Specific Folders"
4. Follow the prompts to index folders from your Google Drive
5. After indexing, restart the Streamlit app:
   ```bash
   streamlit run app.py
   ```

---

### 5. "Sorry, I encountered an error processing your request"

**Symptom:** Front-end shows connection but queries fail with generic error.

**Common Causes & Fixes:**

#### A. API Key Invalid or Expired
- Check your `.env` file has the correct `GOOGLE_API_KEY`
- Verify the key at: https://aistudio.google.com/app/apikey
- Make sure the key hasn't been revoked
- Restart the application after fixing

#### B. API Quota Exceeded
- Check your usage at: https://aistudio.google.com/app/apikey
- Gemini Flash has generous free tier, but has limits
- Wait for quota to reset or upgrade your plan

#### C. No Documents Indexed
- Run `python main.py` and select option 5 "Check Status"
- If no collections are shown, you need to index folders (see issue #4)

#### D. Network Issues
- Check your internet connection
- Verify you can access: https://generativelanguage.googleapis.com
- Check firewall settings

---

### 6. Python Package Errors

**Symptom:** Import errors or missing modules.

**Fix:**
```bash
# Install/update all dependencies
pip install -r requirements.txt

# If you get conflicts, create a fresh virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

### 7. ChromaDB or Vector Store Errors

**Symptom:** Errors about database, collections, or vector store.

**Fix:**

#### A. Corrupted Database
```bash
# Backup first if you have important data
mv chroma_db chroma_db.backup

# Re-index your folders
python main.py
# Select option 2 to re-index
```

#### B. Collection Not Found
```bash
python main.py
# Select option 5 "Check Status" to see available collections
# Re-index if needed with option 2
```

---

### 8. Token.pickle Errors

**Symptom:** Errors loading or saving authentication token.

**Fix:**
```bash
# Delete the token file
rm token.pickle

# Re-authenticate
python main.py
# Select option 1 "Test Authentication"
# Browser will open for authorization
```

---

## Advanced Troubleshooting

### Enable Debug Mode

To see more detailed error messages:

1. **For Streamlit:**
   ```bash
   streamlit run app.py --logger.level=debug
   ```

2. **For CLI:**
   - Add debug prints in the code where errors occur
   - Check `answer_log.txt` for query logs

### Check Configuration

```bash
python -c "from config import *; print('PROJECT_ID:', PROJECT_ID); print('GOOGLE_API_KEY:', 'SET' if GOOGLE_API_KEY else 'NOT SET')"
```

### Test Components Individually

1. **Test Authentication:**
   ```bash
   python auth.py
   ```

2. **Test Gemini API:**
   ```bash
   python -c "import google.generativeai as genai; from config import GOOGLE_API_KEY; genai.configure(api_key=GOOGLE_API_KEY); print('API Key is valid!')"
   ```

3. **Test Embeddings:**
   ```bash
   python -c "from embeddings import LocalEmbedder; e = LocalEmbedder(); print('Embeddings loaded!')"
   ```

---

## Still Having Issues?

1. Run the validation script:
   ```bash
   python validate_setup.py
   ```

2. Check the logs:
   - `answer_log.txt` - Query logs
   - Streamlit logs in terminal
   - Python error tracebacks

3. Verify all prerequisites:
   - [ ] Python 3.8+ installed
   - [ ] All dependencies installed (`pip install -r requirements.txt`)
   - [ ] `.env` file created with valid `GOOGLE_API_KEY`
   - [ ] `credentials.json` downloaded and placed in project root
   - [ ] Google Drive API enabled in Google Cloud Console
   - [ ] OAuth consent screen configured
   - [ ] At least one folder indexed

4. Try a clean setup:
   ```bash
   # Create fresh virtual environment
   python -m venv venv_new
   source venv_new/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Validate setup
   python validate_setup.py
   ```

---

## Getting Help

When reporting issues, please include:

1. Output from `python validate_setup.py`
2. Python version: `python --version`
3. Operating system
4. Full error message/traceback
5. Steps to reproduce the issue
6. What you've already tried

---

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Missing API key | Create `.env` with `GOOGLE_API_KEY=your_key` |
| Missing credentials | Download `credentials.json` from Google Cloud Console |
| No folders indexed | Run `python main.py`, select option 2 |
| Authentication fails | Delete `token.pickle`, run `python auth.py` |
| Package errors | `pip install -r requirements.txt` |
| Database errors | Delete `chroma_db/` folder and re-index |

---

Last Updated: November 2024
