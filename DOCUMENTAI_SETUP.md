# Document AI Integration - Setup Guide

## What Changed

### New OCR Backend: Google Document AI
- **Replaces**: EasyOCR (local CPU/GPU processing)
- **With**: Google Cloud Document AI (cloud-managed)
- **Benefits**: 
  - No server CPU/GPU load for OCR
  - Better accuracy (especially tables and forms)
  - Faster processing with auto-scaling
  - Handles PDFs natively (no image conversion needed)

## Installation

### 1. Install Required Package
```powershell
pip install google-cloud-documentai
```

### 2. Enable Document AI API
Go to Google Cloud Console and enable Document AI API:
```
https://console.cloud.google.com/apis/library/documentai.googleapis.com?project=rag-chatbot-475316
```

Click **"Enable"** button.

### 3. Create Default Processor (Optional)
Document AI will use a default OCR processor automatically, but you can create a custom one:

1. Go to Document AI Console:
   ```
   https://console.cloud.google.com/ai/document-ai?project=rag-chatbot-475316
   ```

2. Click **"Create Processor"**
3. Choose **"OCR Processor"** or **"Form Parser"**
4. Select region: **"us"** (or "eu", "asia")
5. Copy the **Processor ID** (optional)

### 4. Configuration (Already Done)
File `config.py` has been updated:

```python
# OCR Settings
OCR_BACKEND = "documentai"  # Changed from "easyocr"

# Document AI Settings
DOCUMENTAI_PROJECT_ID = "rag-chatbot-475316"
DOCUMENTAI_LOCATION = "us"
DOCUMENTAI_PROCESSOR_ID = None  # Uses default OCR processor
```

## Usage

### Automatic PDF OCR
When a scanned PDF is uploaded:
1. PyPDF2 tries text extraction first
2. If no text found → **Document AI processes entire PDF**
3. Extracts text with tables, forms, and layout preserved
4. AI enhancement improves quality (if enabled)

### Image OCR
When image files are uploaded (PNG, JPG, etc.):
1. Document AI extracts text directly
2. Preserves structure and formatting
3. Returns confidence scores

## Features

### Advanced Capabilities
- ✅ **Table extraction**: Preserves CSV-like data in PDFs
- ✅ **Form field detection**: Extracts key-value pairs
- ✅ **Layout understanding**: Maintains document structure
- ✅ **Multi-page PDFs**: Processes entire document at once (no image conversion)
- ✅ **Handwriting recognition**: Better than EasyOCR
- ✅ **Multiple languages**: English + many others

### Comparison: Document AI vs EasyOCR

| Feature | Document AI | EasyOCR |
|---------|-------------|---------|
| **Location** | Google Cloud | Your server |
| **CPU/GPU Load** | ✅ Zero | ❌ High |
| **PDF Processing** | ✅ Native | ❌ Convert to images |
| **Table Extraction** | ✅ Yes | ❌ No |
| **Form Detection** | ✅ Yes | ❌ No |
| **Accuracy** | ✅ Higher | ⚠️ Good |
| **Speed** | ✅ Fast | ⚠️ Slow for large PDFs |
| **Scalability** | ✅ Auto-scales | ❌ Server limited |
| **Cost** | ~$1.50/1K pages | $0 API (expensive server) |

## Cost Estimates

### Document AI Pricing
- **OCR Processor**: $1.50 per 1,000 pages
- **Form Parser**: $10 per 1,000 pages (more advanced)

### Example Usage (100 users)
- 50 PDFs/month × 5 pages = 250 pages
- Cost: 250 × $0.0015 = **$0.38/month**

### Monthly Budget (All Cloud Services)
- **Vertex AI Embeddings**: ~$2/month
- **Document AI OCR**: ~$0.50/month
- **Total**: **~$2.50/month** for 100 concurrent users

Compare to: $200-500/month for powerful GPU server

## Testing

### 1. Restart Server
```powershell
# Stop current server (Ctrl+C)
npm start
```

### 2. Upload Test Documents
- Upload a **scanned PDF** (image-based, no text)
- Upload an **image** with text (PNG, JPG)
- Check server logs for: `"Document AI OCR service initialized"`

### 3. Verify Processing
Server logs will show:
```
Document AI OCR service initialized (project: rag-chatbot-475316)
PDF 'document.pdf' appears to be scanned/image-based, attempting OCR...
Using Document AI to process entire PDF: document.pdf
Document AI extracted 2543 characters (confidence: 0.95)
```

## Monitoring Costs

### Google Cloud Console
1. Navigate to: **Billing → Reports**
2. Filter by: **Document AI API**
3. View usage: Pages processed per day/month

### Set Budget Alerts
```powershell
# Already have Vertex AI alerts, add Document AI:
# Go to Billing → Budgets & alerts
# Add Document AI API to existing budget
```

## Rollback to EasyOCR

If needed, revert to local OCR:

```python
# In config.py
OCR_BACKEND = "easyocr"  # Change back from "documentai"
```

Restart server. EasyOCR will load on startup.

## Advanced Configuration

### Custom Processor
If you created a custom processor:
```python
# In config.py
DOCUMENTAI_PROCESSOR_ID = "abc123def456"  # Your processor ID
```

### Different Region
For EU/Asia deployments:
```python
# In config.py
DOCUMENTAI_LOCATION = "eu"  # or "asia"
```

## Troubleshooting

### "Document AI API not enabled"
```
https://console.cloud.google.com/apis/library/documentai.googleapis.com
```
Click "Enable API"

### "Permission denied"
Check that `credentials.json` has Document AI permissions:
- Go to IAM & Admin → Service Accounts
- Ensure service account has role: **"Document AI API User"**

### "Module not found: google.cloud.documentai"
```powershell
pip install google-cloud-documentai
```

### High costs detected
- Check processor type (Form Parser is 6x more expensive than OCR)
- Monitor pages processed in Cloud Console
- Consider setting daily processing limits

## Next Steps

1. ✅ Install: `pip install google-cloud-documentai`
2. ✅ Enable API in Google Cloud Console
3. ✅ Restart server: `npm start`
4. ✅ Test with scanned PDF upload
5. ✅ Monitor costs for first week

## Complete Cloud Architecture

With both Vertex AI and Document AI:
- ✅ **Embeddings**: Cloud (Vertex AI)
- ✅ **OCR**: Cloud (Document AI)
- ✅ **LLM**: Cloud (Gemini via Vertex AI)
- ✅ **Server**: Lightweight request router only

**Result**: True scalability for 100+ concurrent users at ~$2-5/month total cloud cost.

---

**Status**: Ready to use after `pip install google-cloud-documentai` and enabling API
