"""
Pydantic Models/Schemas

This module contains all the Pydantic models for request/response validation.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    """Request model for scraping a TikTok profile."""
    username: str = Field(
        ..., 
        min_length=1, 
        max_length=50, 
        description="TikTok username to scrape"
    )
    process_with_ai: bool = Field(
        default=True, 
        description="Whether to process songs with Gemini AI"
    )


class SongResult(BaseModel):
    """Individual song result from AI processing."""
    song: Optional[str] = None
    artist: Optional[str] = None
    type: str = "unknown"
    confidence: Optional[str] = None
    tiktok_title: str = ""


class ScrapeResponse(BaseModel):
    """Response model for scrape results."""
    username: str
    total_videos_scraped: int
    total_unique_titles: int
    real_songs_identified: int
    raw_titles: list[str]
    processed_songs: Optional[list[SongResult]] = None
    message: str


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str = "TikTok Song Scraper API"
    version: str = "1.0.0"
