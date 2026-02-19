"""
TikTok Song Scraper API Server

FastAPI backend that provides an API endpoint for scraping
TikTok profiles and identifying songs.
"""

import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import TikTokScraper
from processor import SongProcessor

# Thread pool for running sync scraper
executor = ThreadPoolExecutor(max_workers=2)

app = FastAPI(
    title="TikTok Song Scraper API",
    description="Scrape audio/song titles from TikTok profiles and identify real songs using AI",
    version="1.0.0"
)

# Configure CORS for frontend access
# Note: Wildcards don't work with CORS - need explicit origins
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://tik-tok-profile-song-scraper.vercel.app",
]

# Add custom frontend URL from environment if set
frontend_url = os.getenv("FRONTEND_URL", "")
if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    """Request model for scraping a TikTok profile."""
    username: str = Field(..., min_length=1, max_length=50, description="TikTok username to scrape")
    process_with_ai: bool = Field(default=True, description="Whether to process songs with Gemini AI")


class SongResult(BaseModel):
    """Individual song result."""
    song: Optional[str]
    artist: Optional[str]
    type: str
    confidence: Optional[str]
    tiktok_title: str


class ScrapeResponse(BaseModel):
    """Response model for scrape results."""
    username: str
    total_videos_scraped: int
    total_unique_titles: int
    real_songs_identified: int
    raw_titles: list[str]
    processed_songs: Optional[list[SongResult]]
    message: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "TikTok Song Scraper API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check for Cloud Run."""
    return {"status": "healthy"}


def run_scraper(username: str) -> list:
    """Run the scraper in a separate thread (sync code)."""
    scraper = TikTokScraper(username)
    scraper.scrape_songs()
    return scraper.songs


def run_processor(raw_titles: list, api_key: str) -> list:
    """Run the AI processor in a separate thread (sync code)."""
    processor = SongProcessor(api_key)
    processed_results = processor.process_songs(raw_titles)
    return processor.format_song_list(processed_results)


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_profile(request: ScrapeRequest):
    """
    Scrape a TikTok profile for songs.
    
    This endpoint will:
    1. Navigate to the user's TikTok profile
    2. Click through all videos and extract audio titles
    3. Optionally process with Gemini AI to identify real songs
    
    Note: This operation may take several minutes depending on the number of videos.
    """
    username = request.username.strip().lstrip("@")
    
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    
    # Validate username format (basic check)
    if not username.replace("_", "").replace(".", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid username format")
    
    try:
        # Step 1: Scrape the profile (run in thread pool to avoid async/sync conflict)
        loop = asyncio.get_event_loop()
        raw_titles = await loop.run_in_executor(executor, run_scraper, username)
        
        if not raw_titles:
            return ScrapeResponse(
                username=username,
                total_videos_scraped=0,
                total_unique_titles=0,
                real_songs_identified=0,
                raw_titles=[],
                processed_songs=None,
                message="No videos found or could not load the profile. The account may be private or blocked."
            )
        
        # Step 2: Optionally process with AI
        processed_songs = None
        real_songs_count = 0
        
        if request.process_with_ai:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            
            if gemini_api_key:
                # Run AI processing in thread pool
                formatted = await loop.run_in_executor(
                    executor, 
                    run_processor, 
                    raw_titles, 
                    gemini_api_key
                )
                
                processed_songs = [
                    SongResult(
                        song=s.get("song"),
                        artist=s.get("artist"),
                        type=s.get("type", "unknown"),
                        confidence=s.get("confidence"),
                        tiktok_title=s.get("tiktok_title", "")
                    )
                    for s in formatted
                ]
                real_songs_count = len(processed_songs)
            else:
                # No API key, skip processing
                processed_songs = None
        
        return ScrapeResponse(
            username=username,
            total_videos_scraped=len(raw_titles),  # Approximation
            total_unique_titles=len(raw_titles),
            real_songs_identified=real_songs_count,
            raw_titles=raw_titles,
            processed_songs=processed_songs,
            message=f"Successfully scraped {len(raw_titles)} unique audio titles" + 
                    (f" and identified {real_songs_count} real songs" if processed_songs else "")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while scraping: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
