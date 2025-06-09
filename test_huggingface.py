#!/usr/bin/env python3
"""
Test script to verify Hugging Face integration
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_huggingface_models():
    """Test loading Hugging Face models"""
    
    print("🧪 Testing Hugging Face Integration")
    print("=" * 50)
    
    # Test 1: Import dependencies
    try:
        print("📦 Testing imports...")
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        print("✅ Transformers and PyTorch imported successfully")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Load Falconsai model
    try:
        print("\n🤗 Loading Falconsai/text_summarization model...")
        model_name = "Falconsai/text_summarization"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        print("✅ Hugging Face model loaded successfully!")
        
        # Test 3: Generate a summary
        print("\n📝 Testing summarization...")
        test_text = "This is a test article about artificial intelligence and machine learning. AI has revolutionized many industries. Machine learning algorithms can process vast amounts of data."
        
        inputs = tokenizer.encode("summarize: " + test_text, return_tensors="pt", max_length=512, truncation=True)
        
        with torch.no_grad():
            summary_ids = model.generate(
                inputs,
                max_length=150,
                min_length=30,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
        
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        print(f"✅ Generated summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model loading/testing failed: {e}")
        return False

def test_tts():
    """Test TTS functionality"""
    print("\n🎤 Testing TTS Integration")
    print("=" * 30)
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        print("✅ pyttsx3 initialized successfully")
        
        # Test voice properties
        voices = engine.getProperty('voices')
        print(f"✅ Found {len(voices)} voices available")
        
        return True
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 NewsBreeze AI Integration Test")
    print("=" * 60)
    
    hf_success = test_huggingface_models()
    tts_success = test_tts()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"🤗 Hugging Face: {'✅ WORKING' if hf_success else '❌ FAILED'}")
    print(f"🎤 TTS: {'✅ WORKING' if tts_success else '❌ FAILED'}")
    
    if hf_success and tts_success:
        print("\n🎉 ALL AI FEATURES ARE WORKING!")
        print("NewsBreeze is ready with full AI integration!")
    else:
        print("\n⚠️  Some features need attention")
    
    print("=" * 60) 