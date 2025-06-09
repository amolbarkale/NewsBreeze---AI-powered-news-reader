#!/usr/bin/env python3
"""
NewsBreeze Startup Script with Full AI Integration
"""

import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the updated app
from app import app

if __name__ == "__main__":
    print("🚀 Starting NewsBreeze with Full AI Integration")
    print("=" * 60)
    print("📰 RSS Feeds: CNN, NY Times, Washington Post, USA Today, NPR, BBC")
    print("🤗 AI Summarization: Falconsai/text_summarization")
    print("🎤 Voice Synthesis: gTTS + pyttsx3")
    print("🌐 Server: http://localhost:8000")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False) 