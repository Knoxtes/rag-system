"""
Startup validation module for production readiness checks
Validates configuration, dependencies, and environment setup
"""

import os
import sys
from typing import List, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class StartupValidator:
    """Validates system configuration and environment for production deployment"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks
        Returns: (is_valid, errors, warnings)
        """
        self._validate_environment_variables()
        self._validate_file_structure()
        self._validate_credentials()
        self._validate_dependencies()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_environment_variables(self):
        """Check required environment variables"""
        required_vars = ['GOOGLE_API_KEY']
        recommended_vars = ['PROJECT_ID']
        
        for var in required_vars:
            value = os.getenv(var)
            if not value or value == f"your_{var.lower()}_here":
                self.errors.append(f"Required environment variable '{var}' is not set")
        
        for var in recommended_vars:
            value = os.getenv(var)
            if not value or value in ["your-project-id", "your_google_cloud_project_id"]:
                self.warnings.append(f"Recommended environment variable '{var}' is not properly configured")
    
    def _validate_file_structure(self):
        """Check required files and directories"""
        required_files = [
            'config.py',
            'rag_system.py',
            'vector_store.py',
            'embeddings.py',
            'document_loader.py',
            'auth.py',
            '.env.example'
        ]
        
        for file in required_files:
            if not os.path.exists(file):
                self.errors.append(f"Required file '{file}' is missing")
    
    def _validate_credentials(self):
        """Check for credentials files"""
        if not os.path.exists('credentials.json'):
            self.warnings.append(
                "Google OAuth credentials file 'credentials.json' not found. "
                "Download from Google Cloud Console before using Google Drive features."
            )
        
        # Check .env file exists
        if not os.path.exists('.env'):
            self.warnings.append(
                ".env file not found. Copy .env.example to .env and configure your settings."
            )
    
    def _validate_dependencies(self):
        """Check critical Python dependencies"""
        critical_deps = [
            ('chromadb', 'ChromaDB vector database'),
            ('google.generativeai', 'Google Generative AI'),
            ('sentence_transformers', 'Sentence Transformers for embeddings'),
            ('streamlit', 'Streamlit web framework')
        ]
        
        for module_name, description in critical_deps:
            try:
                __import__(module_name)
            except ImportError:
                self.errors.append(
                    f"Required dependency '{module_name}' ({description}) is not installed. "
                    f"Run: pip install -r requirements.txt"
                )
    
    def print_results(self):
        """Print validation results in a formatted way"""
        print("\n" + "=" * 80)
        print("PRODUCTION READINESS VALIDATION")
        print("=" * 80 + "\n")
        
        if self.errors:
            print("❌ ERRORS (Must Fix):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS (Recommended to Fix):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ All validation checks passed!")
            print("   System is ready for production use.")
        elif not self.errors:
            print("✅ No critical errors found.")
            print("   System can run, but please review warnings above.")
        else:
            print("❌ Critical errors found. Please fix before running.")
            print("   System may not function correctly.")
        
        print("\n" + "=" * 80 + "\n")
        
        return len(self.errors) == 0


def validate_startup() -> bool:
    """
    Main validation function
    Returns True if system is ready to run, False otherwise
    """
    validator = StartupValidator()
    is_valid, errors, warnings = validator.validate_all()
    validator.print_results()
    
    return is_valid


if __name__ == "__main__":
    # Run validation
    if not validate_startup():
        sys.exit(1)
    else:
        sys.exit(0)
