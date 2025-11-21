#!/usr/bin/env python3
"""
Production Readiness Verification Script
Checks all critical components before deployment
"""

import os
import sys
import json
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")

def check_mark(passed):
    return f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"

def check_file_exists(filepath, description):
    exists = os.path.exists(filepath)
    print(f"{check_mark(exists)} {description}: {filepath}")
    return exists

def check_env_variable(var_name, is_secret=False):
    from dotenv import load_dotenv
    load_dotenv()
    
    value = os.getenv(var_name)
    exists = value is not None and value != ""
    
    if is_secret and exists:
        # Check if secret has been changed from default
        default_phrases = ['change-this', 'your-super-secret', 'replace-me']
        is_default = any(phrase in value.lower() for phrase in default_phrases)
        status = f"{Colors.YELLOW}⚠ Default value detected{Colors.END}" if is_default else f"{Colors.GREEN}✓ Custom value set{Colors.END}"
        print(f"  {var_name}: {status}")
        return exists and not is_default
    else:
        print(f"{check_mark(exists)} {var_name}: {'Set' if exists else 'Missing'}")
        return exists

def main():
    print_header("RAG SYSTEM - PRODUCTION READINESS CHECK")
    
    all_checks_passed = True
    
    # 1. Critical Files Check
    print(f"{Colors.BOLD}1. Critical Files{Colors.END}")
    critical_files = [
        ('credentials.json', 'Google Cloud credentials'),
        ('.env', 'Environment configuration'),
        ('requirements-production.txt', 'Production requirements'),
        ('passenger_wsgi.py', 'WSGI configuration'),
        ('chat_api.py', 'Flask backend'),
        ('server.js', 'Node.js proxy'),
        ('package.json', 'Node dependencies'),
    ]
    
    for filepath, desc in critical_files:
        if not check_file_exists(filepath, desc):
            all_checks_passed = False
    
    # 2. Frontend Build Check
    print(f"\n{Colors.BOLD}2. Frontend Build{Colors.END}")
    build_path = Path('chat-app/build')
    build_exists = build_path.exists() and build_path.is_dir()
    print(f"{check_mark(build_exists)} React production build")
    
    if build_exists:
        index_html = build_path / 'index.html'
        static_dir = build_path / 'static'
        print(f"  {check_mark(index_html.exists())} index.html")
        print(f"  {check_mark(static_dir.exists())} static/ directory")
    else:
        print(f"  {Colors.YELLOW}⚠ Run 'npm run build' to create production build{Colors.END}")
        all_checks_passed = False
    
    # 3. Environment Variables Check
    print(f"\n{Colors.BOLD}3. Environment Variables{Colors.END}")
    
    # Check critical env vars
    env_checks = [
        ('GOOGLE_CLIENT_ID', False),
        ('GOOGLE_CLIENT_SECRET', True),
        ('ALLOWED_DOMAINS', False),
        ('OAUTH_REDIRECT_URI', False),
        ('FLASK_SECRET_KEY', True),
        ('JWT_SECRET_KEY', True),
    ]
    
    for var_name, is_secret in env_checks:
        if not check_env_variable(var_name, is_secret):
            all_checks_passed = False
    
    # 4. Python Dependencies Check
    print(f"\n{Colors.BOLD}4. Python Dependencies{Colors.END}")
    try:
        import flask
        print(f"{check_mark(True)} Flask {flask.__version__}")
    except ImportError:
        print(f"{check_mark(False)} Flask - Not installed")
        all_checks_passed = False
    
    try:
        import chromadb
        print(f"{check_mark(True)} ChromaDB {chromadb.__version__}")
    except ImportError:
        print(f"{check_mark(False)} ChromaDB - Not installed")
        all_checks_passed = False
    
    try:
        import google.generativeai
        print(f"{check_mark(True)} Google Generative AI")
    except ImportError:
        print(f"{check_mark(False)} Google Generative AI - Not installed")
        all_checks_passed = False
    
    try:
        import sentence_transformers
        print(f"{check_mark(True)} Sentence Transformers")
    except ImportError:
        print(f"{check_mark(False)} Sentence Transformers - Not installed")
        all_checks_passed = False
    
    # 5. Configuration Check
    print(f"\n{Colors.BOLD}5. Configuration Settings{Colors.END}")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        flask_env = os.getenv('FLASK_ENV', 'development')
        debug = os.getenv('DEBUG', 'True').lower() == 'true'
        
        is_production = flask_env == 'production' and not debug
        print(f"{check_mark(is_production)} Production mode: FLASK_ENV={flask_env}, DEBUG={debug}")
        
        if not is_production:
            print(f"  {Colors.YELLOW}⚠ Warning: Not in production mode{Colors.END}")
            print(f"  {Colors.YELLOW}  Set FLASK_ENV=production and DEBUG=False in .env{Colors.END}")
        
    except Exception as e:
        print(f"{check_mark(False)} Configuration check failed: {e}")
        all_checks_passed = False
    
    # 6. Security Warnings
    print(f"\n{Colors.BOLD}6. Security Checks{Colors.END}")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check OAuth redirect URI
    redirect_uri = os.getenv('OAUTH_REDIRECT_URI', '')
    localhost_redirect = 'localhost' in redirect_uri
    if localhost_redirect:
        print(f"  {Colors.YELLOW}⚠ OAUTH_REDIRECT_URI points to localhost{Colors.END}")
        print(f"  {Colors.YELLOW}  Update to your production domain before deploying{Colors.END}")
    else:
        print(f"  {Colors.GREEN}✓ OAUTH_REDIRECT_URI configured for production{Colors.END}")
    
    # Check CORS origins
    cors_origins = os.getenv('CORS_ORIGINS', '')
    has_production_cors = not ('localhost' in cors_origins and len(cors_origins.split(',')) == 1)
    if not has_production_cors:
        print(f"  {Colors.YELLOW}⚠ CORS_ORIGINS only includes localhost{Colors.END}")
        print(f"  {Colors.YELLOW}  Add your production domain to CORS_ORIGINS{Colors.END}")
    else:
        print(f"  {Colors.GREEN}✓ CORS_ORIGINS includes production domains{Colors.END}")
    
    # 7. Node.js Dependencies Check
    print(f"\n{Colors.BOLD}7. Node.js Dependencies{Colors.END}")
    node_modules = Path('node_modules')
    npm_installed = node_modules.exists() and node_modules.is_dir()
    print(f"{check_mark(npm_installed)} Node modules installed")
    
    if not npm_installed:
        print(f"  {Colors.YELLOW}⚠ Run 'npm install' to install Node dependencies{Colors.END}")
        all_checks_passed = False
    
    # 8. Optimization Features Check
    print(f"\n{Colors.BOLD}8. Performance Optimizations{Colors.END}")
    try:
        from config import (
            ENABLE_CONNECTION_POOLING,
            ENABLE_PARALLEL_SEARCH,
            ENABLE_LAZY_LOADING,
            ENABLE_SEMANTIC_CACHE,
            ENABLE_RESPONSE_COMPRESSION
        )
        
        optimizations = [
            ('Connection Pooling', ENABLE_CONNECTION_POOLING),
            ('Parallel Search', ENABLE_PARALLEL_SEARCH),
            ('Lazy Loading', ENABLE_LAZY_LOADING),
            ('Semantic Cache', ENABLE_SEMANTIC_CACHE),
            ('Response Compression', ENABLE_RESPONSE_COMPRESSION),
        ]
        
        for name, enabled in optimizations:
            status = "Enabled" if enabled else "Disabled"
            print(f"  {check_mark(enabled)} {name}: {status}")
        
    except Exception as e:
        print(f"{check_mark(False)} Could not load optimization settings: {e}")
    
    # Final Summary
    print_header("SUMMARY")
    
    if all_checks_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All critical checks passed!{Colors.END}")
        print(f"\n{Colors.GREEN}Your system is ready for production deployment.{Colors.END}")
        print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
        print(f"  1. Upload files to Plesk server")
        print(f"  2. Run: npm install")
        print(f"  3. Run: pip install -r requirements-production.txt")
        print(f"  4. Run: npm run build")
        print(f"  5. Run: npm start")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some checks failed{Colors.END}")
        print(f"\n{Colors.YELLOW}Please address the issues above before deploying.{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
