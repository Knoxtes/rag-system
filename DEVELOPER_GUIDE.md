# Developer Guide - RAG System

## Quick Start for Development

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Cloud Project with Vertex AI enabled
- Google Drive API credentials

### Initial Setup

1. **Clone and Install**
```bash
git clone <repository>
cd rag-system
cp .env.example .env
# Edit .env with your credentials
npm install
pip install -r requirements.txt
```

2. **Configure Environment**
Edit `.env` file:
```bash
GOOGLE_API_KEY=your-api-key
PROJECT_ID=your-project-id
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

3. **Run Development Server**
```bash
# Start both frontend and backend
npm start

# Or start individually:
python chat_api.py  # Backend on port 5000
cd chat-app && npm start  # Frontend on port 3000
```

## Code Quality Standards

### Logging
✅ **DO:** Use app.logger with appropriate levels
```python
app.logger.debug("Detailed debugging info")
app.logger.info("General information")
app.logger.warning("Warning messages")
app.logger.error("Error messages", exc_info=True)
```

❌ **DON'T:** Use print() statements
```python
print("Debug message")  # BAD!
```

### Error Handling
✅ **DO:** Use proper exception handling
```python
from error_handlers import ValidationError, handle_errors

@app.route('/endpoint')
@handle_errors
def my_endpoint():
    if not valid:
        raise ValidationError("Invalid input")
    return jsonify({'success': True})
```

❌ **DON'T:** Return raw exceptions
```python
try:
    # code
except Exception as e:
    return str(e), 500  # BAD!
```

### Input Validation
✅ **DO:** Validate all inputs
```python
from error_handlers import validate_required_fields, validate_string_length

data = request.get_json()
validate_required_fields(data, ['message', 'collection'])
validate_string_length(data['message'], 'message', max_length=10000)
```

❌ **DON'T:** Trust user input
```python
message = data['message']  # No validation - BAD!
```

## Common Tasks

### Adding a New API Endpoint

1. **Define the route with proper decorators:**
```python
from error_handlers import handle_errors
from oauth_config import require_auth
from rate_limiter import limiter

@app.route('/api/new-endpoint', methods=['POST'])
@require_auth
@limiter.limit("30 per minute")
@handle_errors
def new_endpoint():
    """Brief description of what this endpoint does"""
    data = request.get_json()
    
    # Validate inputs
    validate_required_fields(data, ['field1', 'field2'])
    
    # Process request
    result = process_data(data)
    
    # Return response
    return jsonify({'result': result}), 200
```

2. **Add logging:**
```python
app.logger.info(f"New endpoint called with data: {data.get('field1')}")
```

3. **Add tests** (when test suite is available)

### Adding Configuration

1. **Add to config.py:**
```python
# My new feature settings
MY_FEATURE_ENABLED = os.getenv('MY_FEATURE_ENABLED', 'true').lower() == 'true'
MY_FEATURE_TIMEOUT = int(os.getenv('MY_FEATURE_TIMEOUT', '30'))
```

2. **Add to .env.example:**
```bash
# My Feature Configuration
MY_FEATURE_ENABLED=true
MY_FEATURE_TIMEOUT=30
```

3. **Add validation in config.py:**
```python
def validate_config():
    if MY_FEATURE_ENABLED and MY_FEATURE_TIMEOUT < 1:
        errors.append("MY_FEATURE_TIMEOUT must be positive when enabled")
```

### Working with Logging

**Development (console output):**
```python
app.logger.setLevel(logging.DEBUG)
# All logs go to console
```

**Production (file + console):**
```python
app.logger.setLevel(logging.INFO)
# Logs go to logs/rag_system.log and console
```

**Log format:**
```
2025-11-20 10:30:45,123 INFO: User query processed [in chat_api.py:685]
```

## Testing

### Manual Testing

1. **Health Check:**
```bash
curl http://localhost:5000/health
```

2. **Authentication:**
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

3. **Chat Endpoint:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "Test query", "collection": "test"}'
```

### Health Monitoring

Run health check from command line:
```bash
python health_monitor.py
```

Output:
```json
{
  "status": "healthy",
  "memory": {"percent": 45.2},
  "cpu": {"percent": 12.5},
  "disk": {"percent": 60.1},
  "warnings": []
}
```

## Debugging

### Enable Debug Mode

**In .env:**
```bash
FLASK_DEBUG=true
FLASK_ENV=development
```

**Or command line:**
```bash
FLASK_DEBUG=1 python chat_api.py
```

### View Logs

```bash
# Tail application logs
tail -f logs/rag_system.log

# View last 100 lines
tail -100 logs/rag_system.log

# Search for errors
grep ERROR logs/rag_system.log

# Watch logs in real-time with filtering
tail -f logs/rag_system.log | grep -i error
```

### Common Issues

**Issue: "RAG system not initialized"**
```bash
# Check if ChromaDB directory exists
ls -la chroma_db/

# Check if indexed_folders.json exists
cat indexed_folders.json

# Re-run indexing
python reindex_with_vertex.py
```

**Issue: "Google Drive service not available"**
```bash
# Check credentials
ls -la credentials.json token.pickle

# Re-authenticate
python auth.py
```

**Issue: "High memory usage"**
```bash
# Check health
python health_monitor.py

# Restart service
# (automatic on Plesk, manual: kill and restart)
```

## Code Review Checklist

Before submitting code:

- [ ] No print() statements (use app.logger)
- [ ] All inputs validated
- [ ] Error handling with try-catch
- [ ] Proper HTTP status codes
- [ ] Logging at appropriate levels
- [ ] No hardcoded secrets
- [ ] Rate limiting on sensitive endpoints
- [ ] Authentication required where needed
- [ ] Comments for complex logic
- [ ] No commented-out code
- [ ] Files compile without errors

## Performance Tips

### Optimization Guidelines

1. **Use caching effectively:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_operation(param):
    # Your expensive code here
    pass
```

2. **Batch operations when possible:**
```python
# Good: Batch processing
results = process_batch(items)

# Bad: Individual processing
results = [process_item(item) for item in items]
```

3. **Use appropriate log levels:**
```python
# Development
app.logger.debug("Detailed info")  # Only in debug mode

# Production
app.logger.info("Important events")  # Always logged
```

4. **Monitor resource usage:**
```python
from health_monitor import health_monitor

# Log health periodically
health = health_monitor.get_health_status()
app.logger.info(f"Memory: {health['memory']['percent']}%")
```

## Security Best Practices

1. **Never log sensitive data:**
```python
# Bad
app.logger.info(f"API key: {api_key}")

# Good
app.logger.info("API key configured")
```

2. **Validate all external input:**
```python
from error_handlers import validate_file_id

file_id = request.args.get('file_id')
validate_file_id(file_id)  # Raises ValidationError if invalid
```

3. **Use environment variables for secrets:**
```python
# Good
API_KEY = os.getenv('API_KEY')

# Bad
API_KEY = "hardcoded-secret"  # NEVER DO THIS!
```

4. **Sanitize error messages in production:**
```python
from error_handlers import sanitize_error_message

try:
    # code
except Exception as e:
    safe_message = sanitize_error_message(e, app.debug)
    return jsonify({'error': safe_message}), 500
```

## Getting Help

- Check logs: `logs/rag_system.log`
- Run health check: `python health_monitor.py`
- Review security checklist: `SECURITY_CHECKLIST.md`
- Check production readiness: `PRODUCTION_CHECKLIST.md`

## Contributing

1. Create a feature branch
2. Make changes following code quality standards
3. Test thoroughly
4. Submit pull request
5. Address code review feedback

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Python Logging](https://docs.python.org/3/library/logging.html)
