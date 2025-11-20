"""
Environment Configuration Validator
Validates all required environment variables and configurations before startup
"""

import os
import sys
from typing import List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ConfigValidator:
    """Validates production configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.is_production = os.getenv('FLASK_ENV') == 'production'
    
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all configuration
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self._validate_google_oauth()
        self._validate_jwt_config()
        self._validate_google_cloud()
        self._validate_security_settings()
        self._validate_optional_settings()
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_google_oauth(self):
        """Validate Google OAuth configuration"""
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            # Check if credentials.json exists as fallback
            if not os.path.exists('credentials.json'):
                self.errors.append(
                    "Google OAuth credentials not configured. "
                    "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables "
                    "OR provide credentials.json file."
                )
            else:
                self.warnings.append("Using credentials.json instead of environment variables for OAuth")
    
    def _validate_jwt_config(self):
        """Validate JWT configuration"""
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        
        if not jwt_secret:
            if self.is_production:
                self.errors.append(
                    "JWT_SECRET_KEY is required in production. "
                    "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
            else:
                self.warnings.append("JWT_SECRET_KEY not set - using temporary key for development")
        elif len(jwt_secret) < 32:
            self.warnings.append("JWT_SECRET_KEY should be at least 32 characters long for security")
        
        flask_secret = os.getenv('FLASK_SECRET_KEY')
        if not flask_secret:
            if self.is_production:
                self.warnings.append("FLASK_SECRET_KEY not set - sessions may not persist across restarts")
    
    def _validate_google_cloud(self):
        """Validate Google Cloud configuration"""
        api_key = os.getenv('GOOGLE_API_KEY')
        project_id = os.getenv('PROJECT_ID')
        
        if not api_key and not project_id:
            self.warnings.append(
                "Neither GOOGLE_API_KEY nor PROJECT_ID set. "
                "AI features may not work without Google Cloud credentials."
            )
        
        # Check if using Vertex AI
        use_vertex = os.getenv('USE_VERTEX_AI', 'True').lower() == 'true'
        if use_vertex and not project_id:
            self.warnings.append("USE_VERTEX_AI is enabled but PROJECT_ID not set")
    
    def _validate_security_settings(self):
        """Validate security settings"""
        # Check CORS origins
        cors_origins = os.getenv('CORS_ORIGINS', '')
        if not cors_origins and self.is_production:
            self.warnings.append(
                "CORS_ORIGINS not specified. Consider restricting to your domain in production."
            )
        
        # Check allowed domains
        allowed_domains = os.getenv('ALLOWED_DOMAINS', '')
        if not allowed_domains:
            self.warnings.append(
                "ALLOWED_DOMAINS not specified. All authenticated users will be allowed."
            )
    
    def _validate_optional_settings(self):
        """Validate optional settings"""
        # Check token expiry settings
        try:
            token_expiry = int(os.getenv('TOKEN_EXPIRY_HOURS', '168'))
            if token_expiry > 720:  # 30 days
                self.warnings.append(f"TOKEN_EXPIRY_HOURS is very long ({token_expiry} hours)")
        except ValueError:
            self.errors.append("TOKEN_EXPIRY_HOURS must be a valid integer")
        
        try:
            refresh_expiry = int(os.getenv('REFRESH_TOKEN_EXPIRY_DAYS', '30'))
            if refresh_expiry > 90:
                self.warnings.append(f"REFRESH_TOKEN_EXPIRY_DAYS is very long ({refresh_expiry} days)")
        except ValueError:
            self.errors.append("REFRESH_TOKEN_EXPIRY_DAYS must be a valid integer")
    
    def print_report(self):
        """Print validation report"""
        print("\n" + "=" * 80)
        print("CONFIGURATION VALIDATION REPORT")
        print("=" * 80)
        print(f"Environment: {'PRODUCTION' if self.is_production else 'DEVELOPMENT'}")
        print("=" * 80)
        
        if self.errors:
            print("\n❌ ERRORS (must be fixed):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS (recommended to fix):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All configuration checks passed!")
        
        print("\n" + "=" * 80)
        
        if self.errors:
            print("\nConfiguration validation FAILED. Please fix errors before starting.")
            return False
        else:
            if self.warnings:
                print("\nConfiguration validation passed with warnings.")
            return True


def validate_environment():
    """
    Validate environment configuration
    
    Returns:
        True if configuration is valid, False otherwise
    """
    validator = ConfigValidator()
    is_valid, errors, warnings = validator.validate_all()
    validator.print_report()
    
    return is_valid


if __name__ == "__main__":
    # Run validation
    is_valid = validate_environment()
    
    # Exit with error code if validation failed
    sys.exit(0 if is_valid else 1)
