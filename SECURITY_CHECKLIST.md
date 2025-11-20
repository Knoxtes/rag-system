# Security & Production Readiness Checklist

## Pre-Deployment Security Review

### ✅ Authentication & Authorization
- [x] OAuth 2.0 implementation with Google
- [x] JWT tokens with expiry (7 days access, 30 days refresh)
- [x] Secure session management (HttpOnly, SameSite, Secure cookies)
- [x] Domain-based access restrictions
- [x] No hardcoded credentials (all via environment variables)
- [x] Token validation on every protected endpoint
- [x] Refresh token rotation support

### ✅ Input Validation & Sanitization
- [x] Request validation on all endpoints
- [x] Query parameter sanitization
- [x] File upload validation (if applicable)
- [x] ChromaDB query parameterization (prevents injection)
- [x] XSS protection via security headers

### ✅ Security Headers
- [x] X-Content-Type-Options: nosniff
- [x] X-Frame-Options: DENY
- [x] X-XSS-Protection: 1; mode=block
- [x] Strict-Transport-Security (HSTS)
- [x] CORS properly configured

### ✅ Rate Limiting & DDoS Protection
- [x] Per-IP rate limiting (200/day, 50/hour)
- [x] Configurable rate limits
- [x] Protection against brute force attacks
- [x] API endpoint throttling

### ✅ Data Protection
- [x] Sensitive data in environment variables
- [x] .gitignore excludes all credentials
- [x] Secure file permissions recommended
- [x] Encrypted HTTPS connections (via deployment)
- [x] Session data encrypted

### ✅ Error Handling
- [x] No sensitive data in error messages
- [x] Comprehensive exception handling
- [x] Structured logging without secrets
- [x] Production-grade log rotation

### ✅ Dependencies & Updates
- [x] All dependencies specified with versions
- [x] No known vulnerable packages
- [x] Regular update schedule recommended
- [x] Minimal dependency footprint

## Deployment Security Checklist

### Before Deployment
- [ ] Review and update PROJECT_ID in config.py
- [ ] Generate strong random secrets:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Create .env.production with all required variables
- [ ] Ensure credentials.json is NOT in git repository
- [ ] Verify .gitignore excludes all sensitive files
- [ ] Review ALLOWED_DOMAINS configuration
- [ ] Set up Google Cloud project with billing alerts
- [ ] Enable 2FA on Google Cloud account
- [ ] Create service account with minimal required permissions

### During Deployment
- [ ] Use HTTPS only (no HTTP)
- [ ] Set secure file permissions (chmod 600 for sensitive files)
- [ ] Configure firewall rules (only necessary ports open)
- [ ] Set up SSL/TLS certificates
- [ ] Verify security headers are sent
- [ ] Test authentication flow
- [ ] Verify rate limiting works
- [ ] Check CORS configuration

### After Deployment
- [ ] Test authentication with multiple users
- [ ] Verify domain restrictions work
- [ ] Test rate limiting enforcement
- [ ] Check logs for sensitive data leakage
- [ ] Monitor for unusual activity
- [ ] Set up automated security scanning
- [ ] Document security incident response plan
- [ ] Create backup and recovery procedures

## Production Environment Variables

### Required - Security Critical
```bash
# Never use default values in production!
FLASK_SECRET_KEY=<generate-strong-random-key>
JWT_SECRET_KEY=<generate-strong-random-key>
GOOGLE_CLIENT_ID=<your-oauth-client-id>
GOOGLE_CLIENT_SECRET=<your-oauth-client-secret>
```

### Required - Configuration
```bash
FLASK_ENV=production
OAUTH_REDIRECT_URI=https://your-domain.com/auth/callback
ALLOWED_DOMAINS=yourdomain.com,partnerdomain.com
CORS_ORIGINS=https://your-domain.com
```

### Optional - Advanced
```bash
TOKEN_EXPIRY_HOURS=168
REFRESH_TOKEN_EXPIRY_DAYS=30
RATELIMIT_STORAGE_URL=redis://localhost:6379
```

## Security Best Practices

### 1. Secret Management
```bash
# Generate strong secrets
python -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Store in .env.production (NEVER commit)
echo "FLASK_SECRET_KEY=your-secret-here" >> .env.production
echo "JWT_SECRET_KEY=your-secret-here" >> .env.production
chmod 600 .env.production
```

### 2. File Permissions (Linux/Mac)
```bash
# Restrict sensitive files
chmod 600 .env.production
chmod 600 credentials.json
chmod 600 token.pickle
chmod 600 service-account-key.json

# Restrict directories
chmod 755 logs
chmod 755 chroma_db
```

### 3. Firewall Configuration
```bash
# Only allow necessary ports
sudo ufw allow 80/tcp   # HTTP (will redirect to HTTPS)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 22/tcp   # SSH (restrict to your IP if possible)
sudo ufw enable
```

### 4. SSL/TLS Setup (Let's Encrypt)
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
sudo certbot renew --dry-run  # Test auto-renewal
```

### 5. Regular Security Tasks

**Daily:**
- Monitor logs for suspicious activity
- Check for failed authentication attempts

**Weekly:**
- Review access logs
- Check for unusual API usage patterns
- Monitor API costs for anomalies

**Monthly:**
- Update dependencies: `pip install -U -r requirements-unified.txt`
- Review and rotate JWT secrets if needed
- Check for security advisories
- Review user access list

**Quarterly:**
- Security audit of code changes
- Review and update firewall rules
- Test backup and recovery procedures
- Update SSL certificates (auto-renewed by certbot)

## Monitoring & Alerting

### Health Monitoring
```bash
# Set up health check monitoring (external service)
# Ping https://your-domain.com/health every 5 minutes
# Alert if status != "healthy" or response time > 2 seconds
```

### Log Monitoring
```bash
# Monitor for security events
tail -f logs/production.log | grep -E "ERROR|WARN|AUTH_FAILED"

# Set up log aggregation (optional)
# - Splunk
# - ELK Stack
# - Google Cloud Logging
```

### Cost Monitoring
```bash
# Set up Google Cloud billing alerts
# Alert at 50%, 75%, 90%, 100% of budget
# Check daily: curl https://your-domain.com/cost/summary
```

## Incident Response Plan

### 1. Suspected Security Breach
1. **Immediately** rotate all secrets (JWT, Flask, OAuth)
2. Review access logs for unauthorized access
3. Check for data exfiltration
4. Notify affected users if data was compromised
5. Document incident and response
6. Implement additional security measures

### 2. Service Disruption
1. Check health endpoint: `curl https://your-domain.com/health`
2. Review recent logs: `tail -100 logs/production.log`
3. Check system resources: `python system_stats.py`
4. Restart services if needed
5. Investigate root cause
6. Implement preventive measures

### 3. Rate Limit Abuse
1. Identify abusive IP addresses in logs
2. Add IP to blocklist (firewall level)
3. Adjust rate limits if legitimate traffic
4. Consider implementing CAPTCHA for repeated failures
5. Monitor for continued abuse

## Compliance & Privacy

### GDPR Considerations (if applicable)
- [ ] Document what user data is collected
- [ ] Implement data deletion on request
- [ ] Add privacy policy
- [ ] Log user consent
- [ ] Provide data export functionality

### Data Retention
- [ ] Define log retention policy (e.g., 90 days)
- [ ] Define backup retention policy (e.g., 30 days)
- [ ] Implement automated cleanup
- [ ] Document retention policies

## Security Testing

### Manual Testing
```bash
# Test authentication
curl -X POST https://your-domain.com/auth/google

# Test rate limiting (should fail after 50 requests)
for i in {1..60}; do 
  curl https://your-domain.com/health
done

# Test security headers
curl -I https://your-domain.com/health

# Test domain restrictions (should fail)
# Try authenticating with non-allowed domain
```

### Automated Testing
```bash
# Run security scanner
pip install safety
safety check -r requirements-unified.txt

# Check for known vulnerabilities
pip install bandit
bandit -r . -x ./venv,./node_modules

# Dependency audit
npm audit --production
```

## Common Security Issues & Fixes

### Issue: Exposed Secrets in Git History
```bash
# If secrets were committed, they're in git history
# You MUST rotate all exposed secrets immediately
# Use git-secrets to prevent future commits
git secrets --install
git secrets --register-aws
```

### Issue: Weak JWT Secrets
```bash
# Generate new strong secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Update .env.production and restart service
```

### Issue: Unauthorized Access Attempts
```bash
# Review logs
grep "401\|403" logs/production.log

# Block abusive IPs
sudo ufw deny from <IP_ADDRESS>

# Consider adding fail2ban
sudo apt-get install fail2ban
```

## Security Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **Flask Security**: https://flask.palletsprojects.com/en/latest/security/
- **Google Cloud Security**: https://cloud.google.com/security/best-practices
- **Let's Encrypt**: https://letsencrypt.org/
- **Security Headers**: https://securityheaders.com/

## Support Contacts

- **Security Issues**: Report privately to repository owner
- **Google Cloud Support**: https://cloud.google.com/support
- **SSL/TLS Issues**: Let's Encrypt community forum

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Review Schedule**: Quarterly

## Sign-Off

Before going to production, verify all checkboxes above are completed.

**Reviewed by**: _________________  
**Date**: _________________  
**Production deployment approved**: Yes / No
