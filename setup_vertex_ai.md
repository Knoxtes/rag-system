# Setup Vertex AI with Google Cloud Credits

Follow these steps to use your $300 Google Cloud credits:

## 1. Install Vertex AI SDK

```bash
pip install google-cloud-aiplatform
```

## 2. Enable Required APIs in Google Cloud Console

Visit: https://console.cloud.google.com/apis/library

Enable these APIs:
- **Vertex AI API** (search for "Vertex AI API")
- **Generative Language API** (if not already enabled)

## 3. Set Up Authentication

### Option A: Use Application Default Credentials (Recommended)

```bash
gcloud auth application-default login
```

This will open your browser to authenticate. Your credentials will be saved automatically.

### Option B: Use Service Account Key

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=rag-chatbot-475316
2. Click "Create Service Account"
3. Name it: `rag-system-service-account`
4. Grant roles:
   - **Vertex AI User**
   - **Cloud Storage Object Viewer** (if using file storage)
5. Click "Create and Continue"
6. Click "Done"
7. Click on the service account → "Keys" tab
8. "Add Key" → "Create New Key" → JSON format
9. Save the JSON file as `vertex-ai-credentials.json` in your project folder

Then set environment variable:
```bash
# Windows PowerShell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\Notxe\Desktop\rag-system\vertex-ai-credentials.json"

# Windows CMD
set GOOGLE_APPLICATION_CREDENTIALS=C:\Users\Notxe\Desktop\rag-system\vertex-ai-credentials.json

# Linux/Mac
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/vertex-ai-credentials.json"
```

## 4. Verify Your Setup

Run this test script:

```python
import vertexai
from vertexai.generative_models import GenerativeModel

# Initialize
vertexai.init(project="rag-chatbot-475316", location="us-central1")

# Test
model = GenerativeModel("gemini-1.5-flash-002")
response = model.generate_content("Say hello!")
print(response.text)
```

If it works, you'll see "Hello!" response.

## 5. Enable Vertex AI in Your RAG System

In `config.py`, set:
```python
USE_VERTEX_AI = True
```

## 6. Check Your Billing

- View usage: https://console.cloud.google.com/billing/
- Your $300 credit should be active
- Monitor spending to avoid surprises

## Pricing (Using Your Credits)

With Vertex AI on Google Cloud:
- **Gemini 1.5 Flash**: $0.075 per 1M input tokens, $0.30 per 1M output tokens
- **Gemini 1.5 Pro**: $1.25 per 1M input tokens, $5.00 per 1M output tokens

Your $300 credit covers approximately:
- **~4 million Flash queries** (at average 200 tokens per query)
- Much higher limits than free tier!

## Troubleshooting

### "Permission Denied" Error
- Make sure billing is enabled on your project
- Check that Vertex AI API is enabled
- Verify your authentication is set up correctly

### "Project not found"
- Double-check PROJECT_ID in config.py matches your Google Cloud project

### "Model not available in location"
- Try changing LOCATION in config.py to "us-central1" or "us-east1"

## Need Help?

Check the logs in the terminal - they'll show whether it's using:
- `☁️ Using Vertex AI with Google Cloud project: rag-chatbot-475316`
- Or falling back to consumer API
