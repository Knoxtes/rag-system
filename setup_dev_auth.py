"""
Development setup script for testing authentication
Run this to quickly set up environment variables for testing
"""

import os
import secrets

print("=================================")
print("RAG System Development Setup")
print("=================================")

# Create basic environment file for development
env_content = f"""
# Development Environment Variables for RAG System
FLASK_ENV=development
FLASK_SECRET_KEY={secrets.token_urlsafe(32)}
FLASK_DEBUG=True

# Google OAuth Configuration (you need to fill these in)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTH_REDIRECT_URI=http://localhost:5000/auth/callback

# Organization Access Control (optional for development - leave empty to allow all)
ALLOWED_DOMAINS=
JWT_SECRET_KEY={secrets.token_urlsafe(32)}
TOKEN_EXPIRY_HOURS=24

# CORS Configuration
CORS_ORIGINS=http://localhost:3000

# Database Configuration (optional)
DATABASE_URL=sqlite:///rag_system.db

# Google Drive API Configuration (existing)
# Uses your existing credentials.json file

# Rate Limiting (disabled for development)
RATE_LIMIT_STORAGE_URL=

# Logging
LOG_LEVEL=DEBUG
"""

# Write to .env.development
with open('.env.development', 'w') as f:
    f.write(env_content)

print("✅ Created .env.development file")
print("")
print("📋 Next Steps:")
print("1. Get Google OAuth credentials:")
print("   - Go to https://console.cloud.google.com/")
print("   - Create OAuth 2.0 Client ID")
print("   - Add http://localhost:5000/auth/callback as redirect URI")
print("   - Copy Client ID and Secret to .env.development")
print("")
print("2. Update ALLOWED_DOMAINS if you want to restrict access")
print("   - Leave empty to allow any Google account")
print("   - Add comma-separated domains for restriction")
print("")
print("3. Test the authentication:")
print("   - python chat_api.py")
print("   - Visit http://localhost:3000")
print("   - Try logging in with Google")
print("")
print("🔐 For production deployment, see PRODUCTION_DEPLOYMENT.md")