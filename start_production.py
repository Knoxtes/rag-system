#!/usr/bin/env python3
"""
Production Startup Script
Validates configuration and starts the application
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_validator import validate_environment

def main():
    """Main startup function"""
    print("\n🚀 Starting RAG System...")
    print("=" * 80)
    
    # Validate environment configuration
    print("\n📋 Step 1: Validating Configuration...")
    if not validate_environment():
        print("\n❌ Startup aborted due to configuration errors.")
        print("Please fix the errors above and try again.")
        sys.exit(1)
    
    print("\n✅ Configuration validation passed!")
    
    # Import and start the application
    print("\n📦 Step 2: Loading Application...")
    try:
        from chat_api import app, initialize_rag_system
        
        # Initialize RAG system
        print("\n🔧 Step 3: Initializing RAG System...")
        try:
            initialize_rag_system()
            print("✅ RAG System initialized successfully!")
        except Exception as e:
            print(f"⚠️  Warning: RAG system initialization had issues: {e}")
            print("   Server will start with limited functionality")
        
        # Get configuration from environment
        port = int(os.getenv('PORT', '5000'))
        host = os.getenv('HOST', '0.0.0.0')
        is_production = os.getenv('FLASK_ENV') == 'production'
        
        print("\n🌐 Step 4: Starting Web Server...")
        print("=" * 80)
        print(f"Mode: {'PRODUCTION' if is_production else 'DEVELOPMENT'}")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print("=" * 80)
        print("\n✨ Application is ready!")
        print(f"Access at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        print("\n" + "=" * 80 + "\n")
        
        # Start the application
        app.run(
            host=host,
            port=port,
            debug=not is_production,
            use_reloader=not is_production
        )
        
    except ImportError as e:
        print(f"\n❌ Failed to import application: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements-production.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
