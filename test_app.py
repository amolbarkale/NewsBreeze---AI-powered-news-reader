#!/usr/bin/env python3
"""
NewsBreeze Test Script
Tests the main functionality of the application
"""

import requests
import json
import time
import sys

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Models loaded: {data.get('models_loaded')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_news_endpoint():
    """Test the news aggregation endpoint"""
    try:
        print("🔄 Testing news endpoint (this may take a moment)...")
        response = requests.get("http://localhost:8000/api/news", timeout=30)
        if response.status_code == 200:
            data = response.json()
            news_count = len(data.get('news', []))
            print(f"✅ News endpoint working - {news_count} articles loaded")
            if news_count > 0:
                print(f"   Sample article: {data['news'][0]['title'][:50]}...")
            return True
        else:
            print(f"❌ News endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ News endpoint error: {e}")
        return False

def test_voices_endpoint():
    """Test the voices endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/voices", timeout=10)
        if response.status_code == 200:
            data = response.json()
            voices = data.get('voices', [])
            print(f"✅ Voices endpoint working - {len(voices)} voices available")
            for voice in voices:
                print(f"   - {voice['display_name']}")
            return True
        else:
            print(f"❌ Voices endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Voices endpoint error: {e}")
        return False

def test_audio_generation():
    """Test audio generation endpoint"""
    try:
        print("🔄 Testing audio generation (this may take a moment)...")
        payload = {
            "text": "This is a test of the NewsBreeze audio generation system.",
            "voice_name": "celebrity_voice"
        }
        response = requests.post(
            "http://localhost:8000/api/generate-audio",
            json=payload,
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Audio generation working")
                print(f"   Audio URL: {data.get('audio_url')}")
                return True
            else:
                print(f"❌ Audio generation failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Audio generation endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        return False

def main():
    """Main test function"""
    print("🎙️ NewsBreeze Application Test Suite")
    print("=" * 50)
    
    # Wait a moment for the server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("News Aggregation", test_news_endpoint),
        ("Voice Options", test_voices_endpoint),
        ("Audio Generation", test_audio_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        if test_func():
            passed += 1
        time.sleep(2)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! NewsBreeze is working correctly.")
        print("🌐 Open http://localhost:8000 in your browser to use the app")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        print("💡 Make sure all dependencies are installed and models are loaded.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 