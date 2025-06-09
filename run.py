#!/usr/bin/env python3
"""
NewsBreeze - Celebrity-Powered Audio News Reader
Run script to start the application
"""

import uvicorn
import os
import sys

def main():
    """Main function to run the NewsBreeze application"""
    
    print("🎙️ Starting NewsBreeze - Celebrity-Powered Audio News Reader")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    # Check if required files exist
    required_files = ['app.py', 'requirements.txt', 'templates/index.html']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Error: Required file {file} not found")
            sys.exit(1)
    
    print("✅ All required files found")
    print("🚀 Starting FastAPI server...")
    print("📱 Open your browser and navigate to: http://localhost:8000")
    print("🔄 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Import and run the FastAPI app
        from app import app
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 NewsBreeze stopped. Thank you for using our service!")
    except Exception as e:
        print(f"❌ Error starting NewsBreeze: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 