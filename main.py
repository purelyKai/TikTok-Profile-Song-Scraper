"""
TikTok Profile Song Scraper - Main Entry Point

This script scrapes audio titles from a TikTok user's profile and optionally
processes them with Gemini AI to identify real songs.

Usage:
    python main.py                  # Scrape and process (if API key available)
    python main.py --scrape-only    # Only scrape, skip AI processing
    python main.py --process-only   # Only process existing raw_songs.json
"""

import os
import json
import argparse
from dotenv import load_dotenv

from scraper import TikTokScraper
from processor import SongProcessor


def get_output_path(filename):
    """Get the appropriate output path based on environment."""
    # Check if output directory exists (Docker environment)
    output_dir = "/app/output" if os.path.isdir("/app/output") else "."
    return os.path.join(output_dir, filename)


def scrape_tiktok(username, output_file="raw_songs.json"):
    """
    Scrape audio titles from a TikTok user's profile.
    
    Args:
        username (str): TikTok username to scrape.
        output_file (str): Output file for raw titles.
        
    Returns:
        list: List of scraped audio titles.
    """
    print(f"Starting TikTok song scraper for user: {username}")
    print("=" * 50)
    
    scraper = TikTokScraper(username)
    scraper.scrape_songs()
    scraper.save_to_json(get_output_path(output_file))
    
    return scraper.songs


def process_with_ai(raw_titles, api_key, raw_output="processed_songs.json", final_output="songs.json"):
    """
    Process raw audio titles with Gemini AI to identify real songs.
    
    Args:
        raw_titles (list): List of raw audio titles.
        api_key (str): Gemini API key.
        raw_output (str): Output file for full processed results.
        final_output (str): Output file for clean song list.
        
    Returns:
        tuple: (processed_results, formatted_songs)
    """
    print("\n" + "=" * 50)
    print("Processing audio titles with Gemini AI...")
    print("=" * 50)
    
    processor = SongProcessor(api_key)
    processed_results = processor.process_songs(raw_titles)
    
    # Save full processed results
    processor.save_results(processed_results, get_output_path(raw_output))
    
    # Save formatted real songs
    real_songs = processor.save_formatted_songs(processed_results, get_output_path(final_output))
    
    return processed_results, real_songs


def print_summary(total_titles, real_songs):
    """
    Print a summary of the scraping and processing results.
    
    Args:
        total_titles (int): Total number of titles scraped.
        real_songs (list): List of identified real songs.
    """
    real_count = len(real_songs)
    print(f"\n{'=' * 50}")
    print("SUMMARY")
    print(f"{'=' * 50}")
    print(f"Total unique audio titles scraped: {total_titles}")
    print(f"Identified as real songs: {real_count}")
    print(f"User originals/unidentified: {total_titles - real_count}")
    print(f"\nFiles created:")
    print(f"  - raw_songs.json: Raw TikTok audio titles")
    print(f"  - processed_songs.json: Full AI analysis results")
    print(f"  - songs.json: Clean list of real songs")


def main():
    """Main entry point for the TikTok song scraper."""
    # Parse command line arguments
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
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    tiktok_username = args.profile or os.getenv("PROFILE")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    # Validate configuration
    if not args.process_only and not tiktok_username:
        print("Error: PROFILE environment variable not set.")
        print("Please create a .env file with: PROFILE=username")
        print("Or use --profile <username> argument")
        return
    
    raw_titles = []
    
    # Step 1: Scrape (unless --process-only)
    if not args.process_only:
        raw_titles = scrape_tiktok(tiktok_username)
    else:
        # Load existing raw songs
        raw_songs_path = get_output_path("raw_songs.json")
        try:
            with open(raw_songs_path, 'r', encoding='utf-8') as f:
                raw_titles = json.load(f)
            print(f"Loaded {len(raw_titles)} titles from {raw_songs_path}")
        except FileNotFoundError:
            print(f"Error: {raw_songs_path} not found. Run scraper first.")
            return
    
    # Step 2: Process with AI (unless --scrape-only)
    if args.scrape_only:
        print("\nSkipping AI processing (--scrape-only flag set).")
        print("To process later, run: python main.py --process-only")
        return
    
    if not gemini_api_key:
        print("\nNote: GEMINI_API_KEY not set. Skipping AI processing.")
        print("To enable song identification, add GEMINI_API_KEY to your .env file.")
        return
    
    if not raw_titles:
        print("\nNo songs found to process.")
        return
    
    # Process with AI
    processed_results, real_songs = process_with_ai(raw_titles, gemini_api_key)
    
    # Print summary
    print_summary(len(raw_titles), real_songs)


if __name__ == "__main__":
    main()
