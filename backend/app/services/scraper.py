"""
TikTok Profile Scraper Service

This module contains the TikTokScraper class for scraping audio titles
from a TikTok user's profile using Playwright with stealth capabilities.
"""

import os
import time
import random
import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth


class TikTokScraper:
    """
    A class to scrape song data from a TikTok user's profile.
    Uses playwright-stealth to bypass bot detection.
    """
    
    # Selectors for audio/music title
    MUSIC_SELECTORS = [
        'a[data-e2e="browse-music"]',
        'a[data-e2e="video-music"]',
        '[data-e2e="browse-music-name"]',
        'div[class*="DivMusicText"]',
        'div[class*="MusicText"]',
    ]
    
    def __init__(self, username: str):
        """
        Initialize the scraper with a TikTok username.
        
        Args:
            username: The TikTok username to scrape.
        """
        self.username = username
        self.url = f"https://www.tiktok.com/@{self.username}"
        self.songs: list[str] = []
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        self.output_dir = "/app/output" if os.path.isdir("/app/output") else "."

    def _get_screenshot_path(self, filename: str) -> str:
        """Get the appropriate path for saving screenshots."""
        return os.path.join(self.output_dir, filename)

    def _setup_browser(self, playwright):
        """Sets up a browser with stealth settings to avoid bot detection."""
        if self.headless:
            print("Running in headless mode (Docker/CI environment)")
        
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--disable-dev-shm-usage',
            '--disable-browser-side-navigation',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-features=BlockInsecurePrivateNetworkRequests',
            '--window-size=1920,1080',
        ]
        
        if self.headless:
            browser_args.extend([
                '--headless=new',
                '--disable-extensions',
            ])
        
        browser = playwright.chromium.launch(
            headless=self.headless,
            args=browser_args
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/Los_Angeles',
            geolocation={'latitude': 34.0522, 'longitude': -118.2437},
            permissions=['geolocation'],
            color_scheme='light',
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        return browser, context, page

    def _try_load_page(self, page, max_retries: int = 3) -> bool:
        """Try to load the TikTok page with retries."""
        for attempt in range(1, max_retries + 1):
            print(f"Attempt {attempt}/{max_retries} to load page...")
            
            try:
                page.goto(self.url, wait_until='networkidle', timeout=60000)
                time.sleep(random.uniform(2, 3))  # Initial page load delay
                
                try:
                    page.wait_for_selector('div[data-e2e="user-post-item"]', timeout=15000)
                    print("Page loaded successfully! Found video grid.")
                    return True
                except Exception:
                    pass
                
                content = page.content()
                if "Something went wrong" in content:
                    print("TikTok showed error page.")
                else:
                    print("Video grid not found, but no error message detected.")
                
                print(f"Attempt {attempt} failed.")
                
                if attempt < max_retries:
                    wait_time = attempt * 5
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"Error during attempt {attempt}: {e}")
                if attempt < max_retries:
                    time.sleep(5)
        
        return False

    def _get_music_title(self, page) -> str | None:
        """Get the music/audio title. Returns immediately if found."""
        for selector in self.MUSIC_SELECTORS:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    title = element.inner_text(timeout=200)
                    if title and title.strip():
                        return title.strip()
            except Exception:
                continue
        return None

    def _click_next_and_wait_for_change(self, page, current_title: str | None) -> tuple[bool, str | None]:
        """
        Click next and wait for content to change. Returns (success, new_title).
        Waits up to 2 seconds for the title to change, otherwise proceeds.
        """
        next_button = page.locator('button[data-e2e="arrow-right"]')
        
        try:
            # Wait for next button to appear (up to 5 seconds)
            # This handles slow loading / transition between videos
            for i in range(50):
                if next_button.is_visible():
                    break
                time.sleep(0.1)
            else:
                print("Next button not visible after 5 seconds. Reached the end.")
                return False, None
            
            # Check if disabled (last video)
            if next_button.get_attribute('disabled') is not None:
                print("Next button is disabled. Reached the last video.")
                return False, None
            
            # Click next
            next_button.click()
            
            # Wait for title to change (max 2 seconds, check every 100ms)
            for _ in range(20):
                new_title = self._get_music_title(page)
                if new_title and new_title != current_title:
                    return True, new_title
                time.sleep(0.1)
            
            # Title didn't change, but still continue
            return True, self._get_music_title(page)
            
        except Exception as e:
            print(f"Error navigating: {e}")
            return False, None

    def scrape_songs(self, max_videos: int = 1000) -> list[str]:
        """
        Scrapes the songs from the user's profile by clicking through videos.
        Optimized for speed - waits only for necessary elements to load.
        
        Args:
            max_videos: Maximum number of videos to scrape (safety limit).
            
        Returns:
            List of unique song titles found.
        """
        with sync_playwright() as p:
            browser, context, page = self._setup_browser(p)
            
            try:
                print(f"Navigating to {self.url}...")
                
                if not self._try_load_page(page, max_retries=3):
                    print("Could not load page after multiple attempts.")
                    screenshot_path = self._get_screenshot_path("debug_screenshot.png")
                    page.screenshot(path=screenshot_path)
                    print(f"Screenshot saved to {screenshot_path}")
                    
                    html_path = self._get_screenshot_path("debug_page.html")
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(page.content())
                    print(f"HTML saved to {html_path}")
                    return self.songs
                
                # Click on the first video
                print("Clicking on the first video...")
                first_video = page.locator('div[data-e2e="user-post-item"]').first
                first_video.click()
                
                # Wait for video viewer to open
                print("Waiting for video viewer to open...")
                page.wait_for_selector('[data-e2e="browse-video"]', timeout=15000)
                print("Video viewer opened.")
                
                song_titles = set()
                video_count = 0
                current_title = self._get_music_title(page)
                
                while video_count < max_videos:
                    video_count += 1
                    
                    if current_title:
                        if current_title not in song_titles:
                            print(f"[{video_count}] Found: {current_title}")
                            self.songs.append(current_title)
                            song_titles.add(current_title)
                        else:
                            print(f"[{video_count}] Duplicate: {current_title}")
                    else:
                        print(f"[{video_count}] No audio title found")
                    
                    # Click next and wait for new content
                    success, current_title = self._click_next_and_wait_for_change(page, current_title)
                    if not success:
                        break
                
                print(f"\nScraping complete! Found {len(self.songs)} unique songs from {video_count} videos.")

            except Exception as e:
                print(f"An error occurred: {e}")
                try:
                    screenshot_path = self._get_screenshot_path("error_screenshot.png")
                    page.screenshot(path=screenshot_path)
                    print(f"Screenshot saved to {screenshot_path}")
                except Exception:
                    pass
            finally:
                context.close()
                browser.close()
                print("Browser closed.")
        
        return self.songs

    def save_to_json(self, filename: str = "songs.json") -> None:
        """Saves the scraped songs to a JSON file."""
        print(f"Saving {len(self.songs)} songs to {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.songs, f, ensure_ascii=False, indent=4)
        print("Done.")
