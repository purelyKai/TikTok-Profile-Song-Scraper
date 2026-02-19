"""
TikTok Song Scraper API

FastAPI backend that provides an API endpoint for scraping
TikTok profiles and identifying songs.
"""

import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import ScrapeRequest, ScrapeResponse, SongResult, HealthResponse
from app.services.scraper import TikTokScraper
from app.services.processor import SongProcessor

# Thread pool for running sync scraper
executor = ThreadPoolExecutor(max_workers=2)

# FastAPI app
app = FastAPI(
    title="TikTok Song Scraper API",
    description="Scrape audio/song titles from TikTok profiles and identify real songs using AI",
    version="1.0.0"
)

# Configure CORS
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://tik-tok-profile-song-scraper.vercel.app",
]

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


# Helper functions for running sync code in thread pool
def run_scraper(username: str) -> list[str]:
    """Run the scraper in a separate thread (sync code)."""
    scraper = TikTokScraper(username)
    scraper.scrape_songs()
    return scraper.songs


def run_processor(raw_titles: list[str], api_key: str) -> list[dict]:
    """Run the AI processor in a separate thread (sync code)."""
    processor = SongProcessor(api_key)
    processed_results = processor.process_songs(raw_titles)
    return processor.format_song_list(processed_results)


# Routes
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return HealthResponse(status="healthy")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check for Cloud Run."""
    return HealthResponse(status="healthy")


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
    
    if not username.replace("_", "").replace(".", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid username format")
    
    try:
        # Run scraper in thread pool
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
        
        # Process with AI if requested
        processed_songs = None
        real_songs_count = 0
        
        if request.process_with_ai:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            
            if gemini_api_key:
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
        
        return ScrapeResponse(
            username=username,
            total_videos_scraped=len(raw_titles),
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
