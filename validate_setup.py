#!/usr/bin/env python3
"""
Setup Validation Script
Checks all required credentials and configuration before running the application.
"""

import os
import sys
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def check_status(condition, success_msg, failure_msg, fix_msg=None):
    """Check a condition and print status"""
    if condition:
        print(f"{Colors.GREEN}✓{Colors.RESET} {success_msg}")
        return True
    else:
        print(f"{Colors.RED}✗{Colors.RESET} {failure_msg}")
        if fix_msg:
            print(f"  {Colors.YELLOW}→ {fix_msg}{Colors.RESET}")
        return False

def validate_environment():
    """Validate all environment setup requirements"""
    print_header("RAG SYSTEM SETUP VALIDATION")
    
    all_valid = True
    
    # 1. Check for .env file
    print(f"{Colors.BOLD}1. Environment Configuration{Colors.RESET}")
    env_exists = os.path.exists('.env')
    all_valid &= check_status(
        env_exists,
        ".env file found",
        ".env file not found",
        "Copy .env.example to .env and fill in your credentials:\n     cp .env.example .env"
    )
    
    if env_exists:
        # Load .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print(f"  {Colors.GREEN}→ Loaded environment variables from .env{Colors.RESET}")
        except ImportError:
            print(f"  {Colors.YELLOW}→ python-dotenv not found, environment variables may not load{Colors.RESET}")
    
    # 2. Check for GOOGLE_API_KEY
    print(f"\n{Colors.BOLD}2. Google Gemini API Key{Colors.RESET}")
    google_api_key = os.getenv('GOOGLE_API_KEY')
    has_valid_key = google_api_key and google_api_key != 'your_gemini_api_key_here'
    all_valid &= check_status(
        has_valid_key,
        f"GOOGLE_API_KEY is set ({google_api_key[:10] if google_api_key else 'None'}...)",
        "GOOGLE_API_KEY is not set or is placeholder",
        "Get your API key from: https://aistudio.google.com/app/apikey\n     Then add it to your .env file: GOOGLE_API_KEY=your_key_here"
    )
    
    # 3. Check for Google Drive credentials
    print(f"\n{Colors.BOLD}3. Google Drive OAuth Credentials{Colors.RESET}")
    credentials_exists = os.path.exists('credentials.json')
    all_valid &= check_status(
        credentials_exists,
        "credentials.json found",
        "credentials.json not found",
        "Download OAuth credentials from Google Cloud Console:\n"
        "     1. Go to https://console.cloud.google.com/apis/credentials\n"
        "     2. Create OAuth 2.0 Client ID (Desktop app)\n"
        "     3. Download JSON and save as 'credentials.json'"
    )
    
    # 4. Check for token.pickle (optional, created on first auth)
    print(f"\n{Colors.BOLD}4. Google Drive Authentication Token{Colors.RESET}")
    token_exists = os.path.exists('token.pickle')
    if token_exists:
        print(f"{Colors.GREEN}✓{Colors.RESET} token.pickle found (already authenticated)")
    else:
        print(f"{Colors.YELLOW}ℹ{Colors.RESET} token.pickle not found (will be created on first authentication)")
        print(f"  {Colors.YELLOW}→ First run will open browser for Google Drive authorization{Colors.RESET}")
    
    # 5. Check for config.py
    print(f"\n{Colors.BOLD}5. Configuration File{Colors.RESET}")
    config_exists = os.path.exists('config.py')
    check_status(
        config_exists,
        "config.py found",
        "config.py not found",
        "Configuration file is missing - this should not happen!"
    )
    
    # 6. Check PROJECT_ID in config
    if config_exists:
        try:
            from config import PROJECT_ID
            project_id_valid = PROJECT_ID and PROJECT_ID not in ['YOUR_PROJECT_ID', 'rag-chatbot-475316']
            check_status(
                project_id_valid,
                f"PROJECT_ID configured: {PROJECT_ID}",
                "PROJECT_ID not configured or using default",
                "Update PROJECT_ID in config.py with your Google Cloud project ID"
            )
        except Exception as e:
            print(f"{Colors.RED}✗{Colors.RESET} Error loading config.py: {e}")
            all_valid = False
    
    # 7. Check required Python packages
    print(f"\n{Colors.BOLD}6. Required Python Packages{Colors.RESET}")
    required_packages = [
        ('streamlit', 'Streamlit'),
        ('google.generativeai', 'Google Generative AI'),
        ('chromadb', 'ChromaDB'),
        ('sentence_transformers', 'Sentence Transformers'),
        ('google.oauth2', 'Google Auth'),
        ('googleapiclient', 'Google API Client'),
    ]
    
    for module_name, display_name in required_packages:
        try:
            __import__(module_name)
            print(f"{Colors.GREEN}✓{Colors.RESET} {display_name}")
        except ImportError:
            print(f"{Colors.RED}✗{Colors.RESET} {display_name} not installed")
            all_valid = False
    
    if not all_valid:
        print(f"\n  {Colors.YELLOW}→ Install all dependencies: pip install -r requirements.txt{Colors.RESET}")
    
    # Print summary
    print_header("VALIDATION SUMMARY")
    
    if all_valid:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All checks passed!{Colors.RESET}")
        print(f"\n{Colors.GREEN}You're ready to run the application:{Colors.RESET}")
        print(f"  • CLI: python main.py")
        print(f"  • Web: streamlit run app.py")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some checks failed!{Colors.RESET}")
        print(f"\n{Colors.RED}Please fix the issues above before running the application.{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Quick Setup Guide:{Colors.RESET}")
        print(f"  1. Copy .env.example to .env")
        print(f"  2. Add your GOOGLE_API_KEY to .env")
        print(f"  3. Download credentials.json from Google Cloud Console")
        print(f"  4. Update PROJECT_ID in config.py")
        print(f"  5. Run: pip install -r requirements.txt")
        print(f"  6. Run this script again: python validate_setup.py")
        return 1

if __name__ == "__main__":
    sys.exit(validate_environment())
