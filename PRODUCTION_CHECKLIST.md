# Production Deployment Checklist

## Pre-Deployment Validation

### Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Set `GOOGLE_API_KEY` with valid Gemini API key
- [ ] Set `PROJECT_ID` with your Google Cloud project ID
- [ ] Set `LOCATION` (default: us-central1)
- [ ] Verify `.env` file is in `.gitignore`

### Google Cloud Setup
- [ ] Create Google Cloud Project
- [ ] Enable Google Drive API
- [ ] Enable Google Gemini API
- [ ] Download OAuth credentials as `credentials.json`
- [ ] Place `credentials.json` in project root
- [ ] Verify `credentials.json` is in `.gitignore`

### Dependencies
- [ ] Install Python 3.8 or higher
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify critical packages installed (run `python startup_validation.py`)

### Security Checks
- [ ] No API keys hardcoded in source code
- [ ] No credentials committed to version control
- [ ] `.gitignore` includes all sensitive files
- [ ] Environment variables properly configured
- [ ] File permissions set correctly for credentials

## Production Configuration

### Performance Optimization
- [ ] `ENABLE_QUERY_CACHE=True` (default)
- [ ] `CACHE_TTL_SECONDS=300` (5 minutes recommended)
- [ ] `TOP_K_RESULTS=20` (balance quality/speed)
- [ ] `MAX_CONTEXT_CHARACTERS=8000` (cost optimized)
- [ ] `USE_HYBRID_SEARCH=True` (better retrieval)

### System Resources
- [ ] Minimum 4GB RAM available
- [ ] Minimum 10GB disk space for vector database
- [ ] GPU optional (CPU works fine for most use cases)
- [ ] Network connectivity to Google APIs

### Logging and Monitoring
- [ ] Create `logs/` directory (auto-created by logging_config)
- [ ] Set `LOG_LEVEL` environment variable (default: INFO)
- [ ] Configure log rotation settings if needed
- [ ] Plan for log file monitoring/archival

## Initial Testing

### Validation Steps
- [ ] Run `python startup_validation.py` - all checks pass
- [ ] Run `python main.py` - option 1 (Test Authentication) works
- [ ] Index a test folder - option 2 completes successfully
- [ ] Test query on indexed data - returns relevant results
- [ ] Test Streamlit UI: `streamlit run app.py`
- [ ] Verify caching works (repeat query faster second time)

### Integration Testing
- [ ] Google Drive authentication flows correctly
- [ ] OAuth token refresh works
- [ ] Documents indexed successfully
- [ ] Vector search returns results
- [ ] LLM generates coherent answers
- [ ] Citations link back to source documents

## Production Deployment

### Web Server Setup (if using Streamlit)
- [ ] Install production WSGI server (gunicorn, uvicorn)
- [ ] Configure reverse proxy (nginx, Apache)
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set appropriate file permissions

### Monitoring and Maintenance
- [ ] Set up log monitoring
- [ ] Configure error alerting
- [ ] Plan for database backups (chroma_db/)
- [ ] Document operational procedures
- [ ] Set up health check endpoint

### Cost Management
- [ ] Monitor Google API usage
- [ ] Set API quota limits
- [ ] Review cache hit rates
- [ ] Optimize context window sizes
- [ ] Track monthly costs

## Post-Deployment

### Documentation
- [ ] Update README with deployment-specific info
- [ ] Document any custom configuration
- [ ] Create user guides if needed
- [ ] Document troubleshooting steps

### Backup and Recovery
- [ ] Backup `.env` file (securely)
- [ ] Backup `credentials.json` (securely)
- [ ] Backup vector database (`chroma_db/`)
- [ ] Backup `indexed_folders.json`
- [ ] Test restore procedure

### Ongoing Maintenance
- [ ] Schedule dependency updates
- [ ] Monitor security advisories
- [ ] Review logs regularly
- [ ] Update documentation as needed
- [ ] Plan for scaling if usage grows

## Troubleshooting

### Common Issues

**"GOOGLE_API_KEY not set"**
- Solution: Add `GOOGLE_API_KEY` to `.env` file

**"credentials.json not found"**
- Solution: Download OAuth credentials from Google Cloud Console

**"Collection is empty"**
- Solution: Run main.py option 2 to index documents first

**"Authentication failed"**
- Solution: Delete `token.pickle` and re-authenticate

**High API costs**
- Solution: Increase `CACHE_TTL_SECONDS`, reduce `MAX_CONTEXT_CHARACTERS`

**Slow queries**
- Solution: Reduce `TOP_K_RESULTS`, enable `USE_HYBRID_SEARCH`

## Security Best Practices

1. **Never commit sensitive files**
   - Always check `.gitignore` before commits
   - Use `git status` to verify

2. **Rotate API keys regularly**
   - Generate new keys every 90 days
   - Revoke old keys after rotation

3. **Limit OAuth scopes**
   - Only request necessary Drive permissions
   - Review scope usage periodically

4. **Secure environment variables**
   - Use secrets manager in production
   - Never expose `.env` file

5. **Monitor access logs**
   - Review authentication attempts
   - Check for unusual API usage patterns

## Support and Resources

- **Documentation**: See README.md
- **Google Cloud Console**: https://console.cloud.google.com
- **Gemini API Keys**: https://aistudio.google.com/app/apikey
- **Issue Tracking**: Use GitHub Issues for bug reports

---

**Last Updated**: 2025-01-18
**Version**: 1.0.0
