# Testing and Validation Guide

## Overview
This guide provides comprehensive testing procedures for the RAG System to ensure production readiness.

## Pre-Deployment Testing

### 1. Environment Validation

**Automated Checks:**
```bash
# Run startup validation
python startup_validation.py
```

**Expected Result:** All checks pass or warnings only.

**Manual Verification:**
- [ ] `.env` file exists and is configured
- [ ] `credentials.json` exists and is valid
- [ ] All required Python packages installed
- [ ] Python version 3.8 or higher

### 2. Code Quality Checks

**Run Quality Checker:**
```bash
python check_quality.py
```

**Expected Result:** All syntax checks pass.

**Manual Code Review:**
- [ ] No hardcoded secrets or credentials
- [ ] Error handling in place for all external calls
- [ ] Input validation for user inputs
- [ ] Logging instead of print statements (for new code)

### 3. Security Scanning

**Dependency Vulnerabilities:**
```bash
# Install safety
pip install safety

# Check for known vulnerabilities
safety check --json
```

**CodeQL Security Analysis:**
Run via GitHub Actions or local CodeQL installation.

**Manual Security Review:**
- [ ] All sensitive files in `.gitignore`
- [ ] API keys loaded from environment
- [ ] OAuth scopes minimized
- [ ] No SQL injection risks
- [ ] No path traversal vulnerabilities

## Functional Testing

### 4. Authentication Tests

**Test Google Drive Authentication:**
```bash
python main.py
# Select option 1: Test Authentication
```

**Expected Result:**
- OAuth flow completes successfully
- `token.pickle` created
- First 5 Drive files listed

**Troubleshooting:**
- If OAuth fails: Delete `token.pickle` and try again
- If credentials not found: Download from Google Cloud Console

### 5. Document Indexing Tests

**Index a Test Folder:**
```bash
python main.py
# Select option 2: Index Specific Folders
# Choose a small test folder (< 10 files)
```

**Expected Result:**
- Folder indexed successfully
- Collection created in ChromaDB
- `indexed_folders.json` updated
- No errors during document processing

**Verify:**
```bash
# Check status
python main.py
# Select option 5: Check Status
```

### 6. Query Tests

**Test Simple Queries:**
```bash
python main.py
# Select option 4: Individual Folder Q&A
# Try queries like:
# - "What documents are available?"
# - "Summarize the main topics"
# - "Find information about [specific topic]"
```

**Expected Result:**
- Relevant answers returned
- Source citations included
- Response time < 10 seconds
- No errors or crashes

**Test Unified System:**
```bash
python main.py
# Select option 3: Unified Q&A System
# Test cross-collection queries
```

### 7. Web Interface Tests

**Start Streamlit App:**
```bash
streamlit run app.py
```

**Test Checklist:**
- [ ] App loads without errors
- [ ] Collection selector shows indexed folders
- [ ] Chat interface accepts input
- [ ] Responses display correctly
- [ ] Citations are clickable (if implemented)
- [ ] Error messages are user-friendly
- [ ] Page doesn't crash on bad input

**Browser Compatibility:**
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari (if available)

### 8. Health Check Tests

**Start Health Check Server:**
```bash
python health_check.py &
HEALTH_PID=$!
```

**Test Endpoints:**
```bash
# Basic health
curl http://localhost:8080/health
# Expected: {"status": "ok", ...}

# Readiness check
curl http://localhost:8080/health/ready
# Expected: {"status": "ready", ...} (may show warnings)

# Liveness check
curl http://localhost:8080/health/live
# Expected: {"status": "alive", ...}

# Metrics (requires psutil)
curl http://localhost:8080/health/metrics
# Expected: System metrics JSON

# Cleanup
kill $HEALTH_PID
```

## Performance Testing

### 9. Response Time Tests

**Measure Query Performance:**
```python
import time
from rag_system import EnhancedRAGSystem
from auth import authenticate_google_drive

# Initialize
drive = authenticate_google_drive()
rag = EnhancedRAGSystem(drive, "test_collection")

# Test query
start = time.time()
result = rag.query("Test query")
elapsed = time.time() - start

print(f"Response time: {elapsed:.2f}s")
# Expected: < 10 seconds for most queries
```

**Benchmark Different Query Types:**
- Simple factual queries: < 5 seconds
- Multi-document synthesis: < 10 seconds
- Cached queries: < 1 second

### 10. Cache Performance Tests

**Test Query Caching:**
```python
# First query (cache miss)
start = time.time()
result1 = rag.query("What is the Q1 report?")
time1 = time.time() - start

# Second identical query (cache hit)
start = time.time()
result2 = rag.query("What is the Q1 report?")
time2 = time.time() - start

print(f"First query: {time1:.2f}s")
print(f"Cached query: {time2:.2f}s")
print(f"Speedup: {time1/time2:.1f}x")
# Expected: Cached queries 5-10x faster
```

### 11. Load Testing

**Simple Load Test:**
```python
import concurrent.futures
from rag_system import EnhancedRAGSystem

def run_query(query):
    rag = EnhancedRAGSystem(drive, "test_collection")
    return rag.query(query)

queries = ["Query 1", "Query 2", "Query 3"] * 10

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(run_query, queries))

print(f"Completed {len(results)} queries")
# Monitor: Memory usage, error rate, average response time
```

## Integration Testing

### 12. End-to-End Test Scenarios

**Scenario 1: New User Setup**
1. Clone repository
2. Install dependencies
3. Configure `.env`
4. Run `python startup_validation.py`
5. Authenticate with Google
6. Index test folder
7. Run test query
8. Launch web interface

**Scenario 2: Document Update**
1. Modify a document in Google Drive
2. Run incremental indexing (if implemented)
3. Query for updated content
4. Verify new content returned

**Scenario 3: Error Recovery**
1. Stop internet connection
2. Try query (should fail gracefully)
3. Restore connection
4. Retry query (should succeed)

## Monitoring and Observability

### 13. Log Analysis

**Check Logs:**
```bash
# View recent logs
tail -f logs/rag_system_*.log

# Search for errors
grep -i error logs/rag_system_*.log

# Check authentication issues
grep -i auth logs/rag_system_*.log
```

**Log Metrics to Monitor:**
- Error rate (should be < 1%)
- Average response time
- Cache hit rate (target: > 20%)
- API call frequency

### 14. Performance Metrics

**Generate Performance Report:**
```python
from performance_monitor import get_performance_monitor

monitor = get_performance_monitor()
monitor.load_metrics()
monitor.print_summary()
```

**Key Metrics:**
- Cache hit rate: > 20%
- Average response time: < 5 seconds
- Error rate: < 1%
- Cost per query: < $0.02

## Production Validation

### 15. Pre-Launch Checklist

**Configuration:**
- [ ] Environment variables set in production environment
- [ ] Secrets stored in secrets manager (not .env)
- [ ] API rate limits configured
- [ ] Monitoring and alerting set up

**Security:**
- [ ] All security scans passed
- [ ] No vulnerabilities in dependencies
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Access logs enabled

**Performance:**
- [ ] Load testing completed
- [ ] Database backups configured
- [ ] Log rotation working
- [ ] Health checks passing
- [ ] Auto-scaling configured (if applicable)

**Documentation:**
- [ ] README updated
- [ ] API documentation current
- [ ] Runbooks created
- [ ] Incident response plan documented
- [ ] User guide available

### 16. Smoke Tests in Production

**After Deployment:**
```bash
# 1. Health check
curl https://your-domain.com/health

# 2. Basic query test
# Access web UI and run a simple query

# 3. Check logs for errors
# Review first 10 minutes of logs

# 4. Monitor metrics
# Verify monitoring dashboards showing data
```

## Continuous Testing

### 17. Automated Testing

**CI/CD Pipeline Tests:**
```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    python -m pytest tests/
    python startup_validation.py
    python check_quality.py
```

**Scheduled Tests:**
- Daily: Dependency vulnerability scan
- Weekly: Full functional test suite
- Monthly: Load testing
- Quarterly: Security audit

### 18. Regression Testing

**Before Each Release:**
- [ ] All existing test cases pass
- [ ] No new critical issues
- [ ] Performance not degraded
- [ ] Documentation updated
- [ ] Changelog updated

## Troubleshooting

### Common Issues

**"GOOGLE_API_KEY not set"**
- Solution: Create `.env` file from `.env.example`
- Add valid API key from Google AI Studio

**"credentials.json not found"**
- Solution: Download from Google Cloud Console
- Enable Drive API first

**"Collection is empty"**
- Solution: Run indexing (option 2 in main.py)
- Verify documents in selected folder

**High response times**
- Check: Network latency to Google APIs
- Check: Vector database size
- Check: Cache configuration
- Solution: Reduce `TOP_K_RESULTS`

**Out of memory**
- Check: Number of documents indexed
- Check: Embedding model size
- Solution: Reduce batch sizes
- Solution: Use smaller embedding model

## Support

For testing issues or questions:
- Check documentation in `/docs`
- Review logs in `/logs`
- See `SECURITY.md` for security issues
- See `PRODUCTION_CHECKLIST.md` for deployment

---

**Last Updated**: 2025-01-18
**Version**: 1.0.0
