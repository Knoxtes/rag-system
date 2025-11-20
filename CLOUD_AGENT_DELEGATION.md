# Cloud Agent Delegation

## Overview

The RAG system uses **cloud agent delegation** to handle AI operations through cloud-based services. This pattern provides flexibility, scalability, and cost optimization.

## Architecture

### Cloud Agent Module (`cloud_agent.py`)

The `CloudAgentDelegate` class provides a centralized abstraction for delegating AI model operations to:

1. **Vertex AI (Google Cloud)** - Primary cloud agent for production
2. **Consumer API** - Fallback for development and testing

### Delegation Flow

```
Application Request
       ↓
get_gemini_model()
       ↓
delegate_to_cloud_agent()
       ↓
CloudAgentDelegate.get_model()
       ↓
    ┌──────────────────┐
    │ USE_VERTEX_AI?   │
    └──────────────────┘
           ↓     ↓
         Yes    No
          ↓      ↓
    Vertex AI  Consumer API
    (Cloud)    (Fallback)
```

## Configuration

Cloud agent delegation is configured in `config.py`:

```python
USE_VERTEX_AI = True  # Enable cloud agent delegation
PROJECT_ID = "your-project-id"  # Google Cloud project
LOCATION = "us-central1"  # Cloud region
```

## API Endpoints

### Check Cloud Agent Status

**GET** `/cloud-agent/status`

Returns information about the current cloud agent configuration:

```json
{
  "status": "success",
  "cloud_agent": {
    "using_cloud_agent": true,
    "cloud_provider": "Google Cloud Vertex AI",
    "project_id": "rag-chatbot-475316",
    "location": "us-central1",
    "initialized": true
  }
}
```

## Usage

### In Python Code

```python
from cloud_agent import delegate_to_cloud_agent, get_cloud_agent

# Delegate model creation to cloud agent
model = delegate_to_cloud_agent("gemini-2.5-flash")

# Get cloud agent info
agent = get_cloud_agent()
info = agent.get_delegation_info()
print(f"Using cloud agent: {info['using_cloud_agent']}")
```

### In RAG System

The `rag_system.py` automatically uses cloud agent delegation:

```python
def get_gemini_model(model_name=None):
    """Delegates to cloud agent for model initialization."""
    return delegate_to_cloud_agent(model_name)
```

## Benefits

1. **Centralized Configuration**: Single point for cloud service configuration
2. **Automatic Fallback**: Gracefully falls back to consumer API if Vertex AI unavailable
3. **Cost Optimization**: Uses Google Cloud credits when available
4. **Scalability**: Cloud-based infrastructure scales automatically
5. **Transparency**: Clear logging and status reporting

## Cloud Provider Features

### Vertex AI (Google Cloud)

- ✅ Uses Google Cloud billing and credits
- ✅ Higher rate limits
- ✅ Better for production environments
- ✅ Integrated with Google Cloud ecosystem
- ✅ Enhanced security and compliance

### Consumer API (Fallback)

- ✅ Simple API key authentication
- ✅ Good for development and testing
- ⚠️ Lower rate limits
- ⚠️ Requires GOOGLE_API_KEY environment variable

## Monitoring

Cloud agent delegation provides detailed logging:

```
☁️  Cloud Agent: Delegating to Vertex AI (Project: rag-chatbot-475316)
📦 Cloud Agent Model: gemini-2.5-flash
```

## Troubleshooting

### Vertex AI Not Available

If Vertex AI is not installed:
```bash
pip install google-cloud-aiplatform
```

### Configuration Issues

1. Ensure `USE_VERTEX_AI = True` in `config.py`
2. Set valid `PROJECT_ID` and `LOCATION`
3. Configure Google Cloud credentials
4. Enable Vertex AI API in Google Cloud Console

### Fallback Behavior

If Vertex AI fails, the system automatically falls back to Consumer API:
```
⚠️  Vertex AI not available, falling back to consumer API
🔑 Using Consumer API (fallback) with model: gemini-2.5-flash
```

## Best Practices

1. **Production**: Always use `USE_VERTEX_AI = True` with valid credentials
2. **Development**: Can use Consumer API with `GOOGLE_API_KEY`
3. **Monitoring**: Check `/cloud-agent/status` endpoint regularly
4. **Cost Management**: Vertex AI uses Google Cloud billing - monitor usage
5. **Error Handling**: System handles delegation failures gracefully

## See Also

- `config.py` - Configuration settings
- `cloud_agent.py` - Cloud agent implementation
- `rag_system.py` - RAG system integration
- `VERTEX_AI_MIGRATION.md` - Vertex AI migration guide
