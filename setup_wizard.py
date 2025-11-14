#!/usr/bin/env python3
"""
Quick Setup Helper
Guides users through initial setup interactively.
"""

import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*80)
    print(text.center(80))
    print("="*80 + "\n")

def print_step(number, title):
    print(f"\n{'='*80}")
    print(f"  STEP {number}: {title}")
    print(f"{'='*80}\n")

def check_file_exists(filename):
    return os.path.exists(filename)

def create_env_file():
    """Guide user through creating .env file"""
    print_step(1, "Create .env File")
    
    if check_file_exists('.env'):
        print("✓ .env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Skipping .env creation.")
            return True
    
    print("Creating .env file from template...")
    
    if not check_file_exists('.env.example'):
        print("✗ Error: .env.example not found!")
        return False
    
    # Read template
    with open('.env.example', 'r') as f:
        template = f.read()
    
    print("\n" + "-"*80)
    print("We'll now set up your environment variables.")
    print("-"*80)
    
    # Get GOOGLE_API_KEY
    print("\n📝 Google Gemini API Key")
    print("Get your free API key from: https://aistudio.google.com/app/apikey")
    api_key = input("Enter your GOOGLE_API_KEY (or press Enter to skip): ").strip()
    
    if api_key:
        template = template.replace('your_gemini_api_key_here', api_key)
        print("✓ API key will be saved to .env")
    else:
        print("⚠️  Skipped - you'll need to add this later")
    
    # Get PROJECT_ID
    print("\n📝 Google Cloud Project ID (optional)")
    print("You can find this in Google Cloud Console")
    project_id = input("Enter your PROJECT_ID (or press Enter to skip): ").strip()
    
    if project_id:
        template = template.replace('your_google_cloud_project_id', project_id)
        print("✓ Project ID will be saved to .env")
    
    # Save .env file
    with open('.env', 'w') as f:
        f.write(template)
    
    print("\n✓ .env file created successfully!")
    return True

def setup_google_drive_credentials():
    """Guide user through Google Drive credentials setup"""
    print_step(2, "Set Up Google Drive Credentials")
    
    if check_file_exists('credentials.json'):
        print("✓ credentials.json already exists!")
        return True
    
    print("You need to download OAuth credentials from Google Cloud Console.")
    print("\nFollow these steps:")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Create or select a project")
    print("3. Enable Google Drive API:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Google Drive API'")
    print("   - Click 'Enable'")
    print("4. Create OAuth 2.0 Client ID:")
    print("   - Click 'Create Credentials' > 'OAuth client ID'")
    print("   - Application type: Desktop app")
    print("   - Download the JSON file")
    print("5. Save it as 'credentials.json' in this directory")
    
    input("\nPress Enter once you've downloaded and saved credentials.json...")
    
    if check_file_exists('credentials.json'):
        print("✓ credentials.json found!")
        return True
    else:
        print("✗ credentials.json not found. Please complete this step manually.")
        return False

def install_dependencies():
    """Guide user through installing dependencies"""
    print_step(3, "Install Python Dependencies")
    
    print("Installing required packages...")
    print("This may take a few minutes...\n")
    
    try:
        # Check if in virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if not in_venv:
            print("⚠️  WARNING: You're not in a virtual environment!")
            print("It's recommended to use a virtual environment.")
            create_venv = input("Create a virtual environment now? (Y/n): ").strip().lower()
            
            if create_venv != 'n':
                print("\nCreating virtual environment...")
                subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
                print("✓ Virtual environment created!")
                print("\nTo activate it:")
                if sys.platform == "win32":
                    print("  venv\\Scripts\\activate")
                else:
                    print("  source venv/bin/activate")
                print("\nThen run this setup script again.")
                return False
        
        # Install dependencies
        print("Installing dependencies from requirements.txt...")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Dependencies installed successfully!")
            return True
        else:
            print("✗ Error installing dependencies:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nPlease install manually:")
        print("  pip install -r requirements.txt")
        return False

def validate_setup():
    """Run validation script"""
    print_step(4, "Validate Setup")
    
    print("Running setup validation...")
    try:
        result = subprocess.run([sys.executable, 'validate_setup.py'], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode == 0:
            return True
        else:
            print("\nSome checks failed. Please fix the issues above.")
            return False
    except Exception as e:
        print(f"✗ Error running validation: {e}")
        return False

def main():
    print_header("RAG SYSTEM QUICK SETUP")
    
    print("This wizard will help you set up the RAG system.")
    print("You can press Ctrl+C at any time to exit.\n")
    
    input("Press Enter to continue...")
    
    # Step 1: Create .env
    if not create_env_file():
        print("\n✗ Setup incomplete. Please fix errors and try again.")
        return 1
    
    # Step 2: Google Drive credentials
    if not setup_google_drive_credentials():
        print("\n⚠️  You'll need to complete Google Drive setup manually.")
        print("Run 'python validate_setup.py' to check your setup.")
    
    # Step 3: Install dependencies
    print("\nDo you want to install Python dependencies now?")
    install = input("This may take several minutes (Y/n): ").strip().lower()
    
    if install != 'n':
        if not install_dependencies():
            print("\n⚠️  Dependency installation incomplete.")
            print("You may need to install them manually: pip install -r requirements.txt")
    
    # Step 4: Validate
    print("\nDo you want to validate your setup now?")
    validate = input("This will check all requirements (Y/n): ").strip().lower()
    
    if validate != 'n':
        validate_setup()
    
    # Final message
    print_header("SETUP COMPLETE!")
    
    print("Next steps:")
    print("1. If validation found issues, fix them following the instructions")
    print("2. Run the CLI: python main.py")
    print("3. Select option 2 to index Google Drive folders")
    print("4. Start chatting with option 3 (CLI) or: streamlit run app.py (Web)")
    
    print("\n📚 Documentation:")
    print("  - README.md - Full documentation")
    print("  - TROUBLESHOOTING.md - Solutions to common problems")
    print("  - validate_setup.py - Check your configuration anytime")
    
    print("\n✨ Happy coding!\n")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
