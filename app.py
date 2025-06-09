from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
import feedparser
import requests
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
from pydantic import BaseModel
import re
from bs4 import BeautifulSoup
import logging

# Hugging Face and TTS imports
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import pyttsx3
from gtts import gTTS
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NewsBreeze", description="Celebrity-Powered Audio News Reader")

# Create directories
os.makedirs("static/audio", exist_ok=True)
os.makedirs("static/voices", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic models
class NewsItem(BaseModel):
    title: str
    summary: str
    original_content: str
    url: str
    published: str
    source: str
    audio_file: Optional[str] = None

class VoiceRequest(BaseModel):
    text: str
    voice_name: str = "celebrity_voice"

# Global variables
news_cache = {}
CACHE_DURATION = 3600  # 1 hour

# AI Models - Global variables for model loading
summarizer_model = None
summarizer_tokenizer = None
tts_engine = None

# Updated RSS Feed sources with the ones you provided
RSS_FEEDS = {
    "CNN": "http://rss.cnn.com/rss/cnn_topstories.rss",
    "New York Times": "http://feeds.nytimes.com/nyt/rss/HomePage",
    "Washington Post": "http://www.washingtonpost.com/rss/",
    "USA Today": "http://rssfeeds.usatoday.com/usatoday-NewsTopStories",
    "NPR": "http://www.npr.org/rss/rss.php?id=1001",
    "BBC News": "http://newsrss.bbc.co.uk/rss/newsonline_world_edition/americas/rss.xml",
}

def load_ai_models():
    """Load Hugging Face models for summarization and TTS"""
    global summarizer_model, summarizer_tokenizer, tts_engine
    
    try:
        logger.info("🤗 Loading Hugging Face summarization model: Falconsai/text_summarization")
        
        # Load Falconsai/text_summarization model
        model_name = "Falconsai/text_summarization"
        summarizer_tokenizer = AutoTokenizer.from_pretrained(model_name)
        summarizer_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        logger.info("✅ Hugging Face summarization model loaded successfully")
        
        # Initialize TTS engine
        logger.info("🎤 Initializing TTS engine")
        try:
            tts_engine = pyttsx3.init()
            # Configure TTS settings
            tts_engine.setProperty('rate', 150)  # Speed of speech
            tts_engine.setProperty('volume', 0.9)  # Volume level
            logger.info("✅ TTS engine initialized successfully")
        except Exception as tts_error:
            logger.warning(f"TTS engine initialization failed: {tts_error}")
            tts_engine = None
        
    except Exception as e:
        logger.error(f"❌ Error loading AI models: {e}")
        logger.info("Falling back to simple mode")

def clean_text(text: str) -> str:
    """Clean and prepare text for processing"""
    if not text:
        return ""
    
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    return text

async def fetch_rss_feed(url: str, source_name: str) -> List[Dict]:
    """Fetch and parse RSS feed"""
    try:
        logger.info(f"📡 Fetching RSS feed from {source_name}: {url}")
        
        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        articles = []
        
        logger.info(f"Found {len(feed.entries)} entries in {source_name}")
        
        for entry in feed.entries[:5]:  # Limit to 5 articles per source
            try:
                # Extract content
                content = ""
                if hasattr(entry, 'content') and entry.content:
                    content = entry.content[0].value
                elif hasattr(entry, 'summary'):
                    content = entry.summary
                elif hasattr(entry, 'description'):
                    content = entry.description
                else:
                    content = entry.title  # Fallback to title
                
                content = clean_text(content)
                
                # Skip if content is too short
                if len(content) < 50:
                    continue
                
                # Extract publication date
                published = ""
                if hasattr(entry, 'published'):
                    published = entry.published
                elif hasattr(entry, 'updated'):
                    published = entry.updated
                else:
                    published = str(datetime.now())
                
                article = {
                    "title": clean_text(entry.title),
                    "content": content,
                    "url": entry.link if hasattr(entry, 'link') else "",
                    "published": published,
                    "source": source_name
                }
                articles.append(article)
                logger.info(f"Added article: {article['title'][:50]}...")
                
            except Exception as e:
                logger.error(f"Error processing entry from {source_name}: {e}")
                continue
            
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching RSS feed {source_name} ({url}): {e}")
        return []

def huggingface_summarize(text: str) -> str:
    """Summarize text using Hugging Face Falconsai/text_summarization model"""
    global summarizer_model, summarizer_tokenizer
    
    try:
        if summarizer_model is None or summarizer_tokenizer is None:
            logger.warning("Summarization model not loaded, falling back to simple summarization")
            return simple_summarize(text)
        
        # Prepare text for summarization
        if len(text) > 1024:  # Truncate if too long
            text = text[:1024]
        
        # Tokenize and generate summary
        inputs = summarizer_tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=512, truncation=True)
        
        with torch.no_grad():
            summary_ids = summarizer_model.generate(
                inputs,
                max_length=150,
                min_length=30,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True
            )
        
        summary = summarizer_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        logger.info(f"✅ Generated summary using Hugging Face Falconsai/text_summarization model")
        return summary
        
    except Exception as e:
        logger.error(f"Error in Hugging Face summarization: {e}")
        return simple_summarize(text)

def simple_summarize(text: str) -> str:
    """Simple text summarization by taking first few sentences (fallback)"""
    try:
        if not text:
            return "No content available."
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        # Take first 2-3 sentences
        summary_sentences = [s.strip() for s in sentences[:3] if s.strip()]
        summary = '. '.join(summary_sentences)
        
        # Add period if not present
        if summary and not summary.endswith('.'):
            summary += '.'
        
        # Ensure it's not too long
        if len(summary) > 300:
            summary = summary[:300] + "..."
        
        return summary if summary else text[:200] + "..."
        
    except Exception as e:
        logger.error(f"Error summarizing text: {e}")
        return text[:200] + "..." if len(text) > 200 else text

def generate_celebrity_voice(text: str, voice_name: str) -> str:
    """Generate audio using TTS with celebrity voice simulation"""
    global tts_engine
    
    try:
        # Create unique filename
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        audio_filename = f"news_{voice_name}_{text_hash}.wav"
        audio_path = f"static/audio/{audio_filename}"
        
        logger.info(f"🎤 Generating audio with {voice_name} voice")
        
        # Try gTTS first (Google Text-to-Speech)
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(audio_path)
            logger.info(f"✅ Audio generated successfully using gTTS: {audio_filename}")
            return f"/static/audio/{audio_filename}"
        except Exception as gtts_error:
            logger.warning(f"gTTS failed: {gtts_error}, trying pyttsx3")
        
        # Fallback to pyttsx3
        if tts_engine:
            # Configure voice based on celebrity selection
            voices = tts_engine.getProperty('voices')
            if voices:
                # Select voice based on celebrity preference
                voice_index = 0
                if voice_name in ['morgan_freeman', 'barack_obama']:
                    # Prefer male voices
                    for i, voice in enumerate(voices):
                        if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                            voice_index = i
                            break
                elif voice_name in ['winston_churchill']:
                    # Prefer British/formal voices
                    for i, voice in enumerate(voices):
                        if 'british' in voice.name.lower() or 'uk' in voice.name.lower():
                            voice_index = i
                            break
                
                tts_engine.setProperty('voice', voices[voice_index].id)
            
            # Adjust speech rate based on character
            if voice_name == 'stephen_hawking':
                tts_engine.setProperty('rate', 120)  # Slower
            elif voice_name == 'david_attenborough':
                tts_engine.setProperty('rate', 140)  # Measured pace
            else:
                tts_engine.setProperty('rate', 150)  # Normal pace
            
            tts_engine.save_to_file(text, audio_path)
            tts_engine.runAndWait()
            
            logger.info(f"✅ Audio generated successfully using pyttsx3: {audio_filename}")
            return f"/static/audio/{audio_filename}"
        
        logger.warning("No TTS engine available")
        return None
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return None

@app.on_event("startup")
async def startup_event():
    """Load AI models on startup"""
    logger.info("🚀 Starting NewsBreeze with Hugging Face AI integration")
    load_ai_models()

@app.get("/")
async def home(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/news")
async def get_news():
    """Fetch and return latest news with AI-powered summaries"""
    try:
        cache_key = "latest_news"
        current_time = datetime.now().timestamp()
        
        # Check cache
        if cache_key in news_cache:
            cache_time, cached_news = news_cache[cache_key]
            if current_time - cache_time < CACHE_DURATION:
                logger.info("Returning cached news")
                return {"news": cached_news, "cached": True}
        
        logger.info("📰 Fetching fresh news from RSS feeds")
        all_articles = []
        
        # Fetch from all RSS sources
        for source_name, rss_url in RSS_FEEDS.items():
            try:
                articles = await fetch_rss_feed(rss_url, source_name)
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} articles from {source_name}")
            except Exception as e:
                logger.error(f"Failed to fetch from {source_name}: {e}")
                continue
        
        logger.info(f"Total articles fetched: {len(all_articles)}")
        
        # Process articles with AI summarization
        processed_articles = []
        for i, article in enumerate(all_articles[:20]):  # Limit to 20 total articles
            try:
                # Use Hugging Face model for summarization
                summary = huggingface_summarize(article["content"])
                
                news_item = NewsItem(
                    title=article["title"],
                    summary=summary,
                    original_content=article["content"],
                    url=article["url"],
                    published=article["published"],
                    source=article["source"]
                )
                processed_articles.append(news_item.dict())
                
            except Exception as e:
                logger.error(f"Error processing article {i}: {e}")
                continue
        
        # Cache the results
        news_cache[cache_key] = (current_time, processed_articles)
        
        logger.info(f"Returning {len(processed_articles)} processed articles with Hugging Face AI summaries")
        return {"news": processed_articles, "cached": False}
        
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

@app.post("/api/generate-audio")
async def generate_audio_endpoint(voice_request: VoiceRequest):
    """Generate audio using TTS with celebrity voice simulation"""
    try:
        logger.info(f"🎤 Audio generation requested for voice: {voice_request.voice_name}")
        
        # Generate audio using TTS
        audio_url = generate_celebrity_voice(voice_request.text, voice_request.voice_name)
        
        if audio_url:
            return {
                "audio_url": audio_url,
                "success": True,
                "message": f"Audio generated successfully with {voice_request.voice_name} voice using AI TTS!"
            }
        else:
            return {
                "audio_url": None,
                "success": False,
                "message": "Failed to generate audio. TTS engine may not be available."
            }
            
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail="Error generating audio")

@app.get("/api/voices")
async def get_available_voices():
    """Get list of available celebrity voices"""
    voices = [
        {"name": "morgan_freeman", "display_name": "Morgan Freeman"},
        {"name": "david_attenborough", "display_name": "David Attenborough"},
        {"name": "barack_obama", "display_name": "Barack Obama"},
        {"name": "stephen_hawking", "display_name": "Stephen Hawking"},
        {"name": "winston_churchill", "display_name": "Winston Churchill"},
    ]
    return {"voices": voices}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    model_status = {
        "summarizer": "loaded" if summarizer_model is not None else "not_loaded",
        "tts": "loaded" if tts_engine is not None else "not_loaded"
    }
    
    return {
        "status": "healthy",
        "models_loaded": model_status,
        "rss_feeds": list(RSS_FEEDS.keys()),
        "ai_features": {
            "huggingface_summarization": "Falconsai/text_summarization",
            "voice_synthesis": "gTTS + pyttsx3"
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 