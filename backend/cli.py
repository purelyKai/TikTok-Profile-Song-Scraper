"""
TikTok Profile Song Scraper - CLI Entry Point

This script scrapes audio titles from a TikTok user's profile and optionally
processes them with Gemini AI to identify real songs.

Usage:
    python cli.py                  # Scrape and process (if API key available)
    python cli.py --scrape-only    # Only scrape, skip AI processing
    python cli.py --process-only   # Only process existing raw_songs.json
    python cli.py --profile user   # Scrape specific user
"""

import os
import json
import argparse
from dotenv import load_dotenv

from app.services.scraper import TikTokScraper
from app.services.processor import SongProcessor


def get_output_path(filename: str) -> str:
    """Get the appropriate output path based on environment."""
    output_dir = "/app/output" if os.path.isdir("/app/output") else "output"
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, filename)


def scrape_tiktok(username: str, output_file: str = "raw_songs.json") -> list[str]:
    """Scrape audio titles from a TikTok user's profile."""
    print(f"Starting TikTok song scraper for user: {username}")
    print("=" * 50)
    
    scraper = TikTokScraper(username)
    scraper.scrape_songs()
    scraper.save_to_json(get_output_path(output_file))
    
    return scraper.songs


def process_with_ai(
    raw_titles: list[str], 
    api_key: str, 
    raw_output: str = "processed_songs.json", 
    final_output: str = "songs.json"
) -> tuple[list[dict], list[dict]]:
    """Process raw audio titles with Gemini AI to identify real songs."""
    print("\n" + "=" * 50)
    print("Processing audio titles with Gemini AI...")
    print("=" * 50)
    
    processor = SongProcessor(api_key)
    processed_results = processor.process_songs(raw_titles)
    
    processor.save_results(processed_results, get_output_path(raw_output))
    real_songs = processor.save_formatted_songs(processed_results, get_output_path(final_output))
    
    return processed_results, real_songs


def print_summary(total_titles: int, real_songs: list[dict]) -> None:
    """Print a summary of the scraping and processing results."""
    real_count = len(real_songs)
    print(f"\n{'=' * 50}")
    print("SUMMARY")
    print(f"{'=' * 50}")
    print(f"Total unique audio titles scraped: {total_titles}")
    print(f"Identified as real songs: {real_count}")
    print(f"User originals/unidentified: {total_titles - real_count}")
    print(f"\nFiles created in output/:")
    print(f"  - raw_songs.json: Raw TikTok audio titles")
    print(f"  - processed_songs.json: Full AI analysis results")
    print(f"  - songs.json: Clean list of real songs")


def main():
    """Main entry point for the TikTok song scraper CLI."""
    parser = argparse.ArgumentParser(
        description="Scrape and identify songs from a TikTok user's profile"
    )
    parser.add_argument(
        '--scrape-only',
        action='store_true',
        help='Only scrape audio titles, skip AI processing'
    )
    parser.add_argument(
        '--process-only',
        action='store_true',
        help='Only process existing raw_songs.json with AI'
    )
    parser.add_argument(
        '--profile',
        type=str,
        help='TikTok username to scrape (overrides .env)'
    )
    args = parser.parse_args()
    
    load_dotenv()
    
    tiktok_username = args.profile or os.getenv("PROFILE")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if not args.process_only and not tiktok_username:
        print("Error: PROFILE environment variable not set.")
        print("Please create a .env file with: PROFILE=username")
        print("Or use --profile <username> argument")
        return
    
    raw_titles = []
    
    if not args.process_only:
        raw_titles = scrape_tiktok(tiktok_username)
    else:
        raw_songs_path = get_output_path("raw_songs.json")
        try:
            with open(raw_songs_path, 'r', encoding='utf-8') as f:
                raw_titles = json.load(f)
            print(f"Loaded {len(raw_titles)} titles from {raw_songs_path}")
        except FileNotFoundError:
            print(f"Error: {raw_songs_path} not found. Run scraper first.")
            return
    
    if args.scrape_only:
        print("\nSkipping AI processing (--scrape-only flag set).")
        print("To process later, run: python cli.py --process-only")
        return
    
    if not gemini_api_key:
        print("\nNote: GEMINI_API_KEY not set. Skipping AI processing.")
        print("To enable song identification, add GEMINI_API_KEY to your .env file.")
        return
    
    if not raw_titles:
        print("\nNo songs found to process.")
        return
    
    processed_results, real_songs = process_with_ai(raw_titles, gemini_api_key)
    print_summary(len(raw_titles), real_songs)


if __name__ == "__main__":
    main()
