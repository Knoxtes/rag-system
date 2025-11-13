# start_chat_system.py - Easy startup script for the complete chat system
import subprocess
import sys
import os
import time

def start_flask_api():
    """Start the Flask API server"""
    print("🚀 Starting Flask API server...")
    try:
        # Install required packages if needed
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'chat-api-requirements.txt'])
        
        # Start the Flask server in background
        api_process = subprocess.Popen(
            [sys.executable, 'chat_api.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return api_process
    except Exception as e:
        print(f"❌ Failed to start Flask API: {e}")
        return None

def start_react_app():
    """Start the React development server"""
    print("🌐 Starting React development server...")
    try:
        # Change to chat-app directory
        os.chdir('chat-app')
        
        # Start the React development server
        react_process = subprocess.Popen(
            ['npm', 'start'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return react_process
    except Exception as e:
        print(f"❌ Failed to start React app: {e}")
        return None

def main():
    print("="*60)
    print("🤖 RAG CHAT SYSTEM STARTUP")
    print("="*60)
    
    # Check if we're in the right directory
    if not os.path.exists('chat_api.py'):
        print("❌ Please run this script from the rag-system directory")
        return
    
    # Start Flask API
    api_process = start_flask_api()
    if not api_process:
        print("❌ Cannot continue without API server")
        return
    
    print("⏳ Waiting for API server to initialize...")
    time.sleep(3)
    
    # Start React app
    react_process = start_react_app()
    if not react_process:
        print("❌ Failed to start React app")
        if api_process:
            api_process.terminate()
        return
    
    print("="*60)
    print("✅ SYSTEM STARTED SUCCESSFULLY!")
    print("="*60)
    print("🔗 Flask API: http://localhost:5000")
    print("🌐 React App: http://localhost:3000")
    print("="*60)
    print("📝 To stop the system:")
    print("   1. Press Ctrl+C in both terminal windows")
    print("   2. Or close this terminal")
    print("="*60)
    
    try:
        # Wait for user to stop
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping system...")
        if api_process:
            api_process.terminate()
        if react_process:
            react_process.terminate()
        print("✅ System stopped")

if __name__ == '__main__':
    main()