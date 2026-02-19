"""
TikTok Profile Scraper Module

This module contains the TikTokScraper class for scraping audio titles
from a TikTok user's profile using Playwright with stealth capabilities.
"""

import os
import time
import random
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


class TikTokScraper:
    """
    A class to scrape song data from a TikTok user's profile.
    Uses playwright-stealth to bypass bot detection.
    """
    
    def __init__(self, username):
        """
        Initialize the scraper with a TikTok username.
        
        Args:
            username (str): The TikTok username to scrape.
        """
        self.username = username
        self.url = f"https://www.tiktok.com/@{self.username}"
        self.songs = []
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        
        # Determine output directory for screenshots
        self.output_dir = "/app/output" if os.path.isdir("/app/output") else "."

    def _random_delay(self, min_sec=1.5, max_sec=3.5):
        """Add a random delay to mimic human behavior."""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _get_screenshot_path(self, filename):
        """Get the appropriate path for saving screenshots."""
        return os.path.join(self.output_dir, filename)

    def _setup_browser(self, playwright):
        """
        Sets up a browser with stealth settings to avoid bot detection.
        """
        if self.headless:
            print("Running in headless mode (Docker/CI environment)")
        
        # More comprehensive args for stealth
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
                '--headless=new',  # Use new headless mode
                '--disable-extensions',
            ])
        
        browser = playwright.chromium.launch(
            headless=self.headless,
            args=browser_args
        )
        
        # Create context with realistic browser fingerprint
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
        
        # Create page and apply stealth
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        return browser, context, page

    def _try_load_page(self, page, max_retries=3):
        """
        Try to load the TikTok page with retries.
        
        Returns:
            bool: True if page loaded successfully, False otherwise.
        """
        for attempt in range(1, max_retries + 1):
            print(f"Attempt {attempt}/{max_retries} to load page...")
            
            try:
                page.goto(self.url, wait_until='networkidle', timeout=60000)
                self._random_delay(2, 4)
                
                # First, try to find the video grid - this is our primary success indicator
                try:
                    page.wait_for_selector('div[data-e2e="user-post-item"]', timeout=15000)
                    print("Page loaded successfully! Found video grid.")
                    return True
                except Exception:
                    pass
                
                # Video grid not found - check if it's an error page
                content = page.content()
                if "Something went wrong" in content:
                    print("TikTok showed error page.")
                else:
                    print("Video grid not found, but no error message detected.")
                
                print(f"Attempt {attempt} failed.")
                
                if attempt < max_retries:
                    wait_time = attempt * 5  # Smaller wait between retries
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"Error during attempt {attempt}: {e}")
                if attempt < max_retries:
                    time.sleep(5)
        
        return False

    def scrape_songs(self, max_videos=1000):
        """
        Scrapes the songs from the user's profile by clicking through videos.
        
        Args:
            max_videos (int): Maximum number of videos to scrape (safety limit).
        """
        with sync_playwright() as p:
            browser, context, page = self._setup_browser(p)
            
            try:
                print(f"Navigating to {self.url}...")
                
                # Try to load the page with retries
                if not self._try_load_page(page, max_retries=3):
                    print("Could not load page after multiple attempts.")
                    print("Taking screenshot for debugging...")
                    screenshot_path = self._get_screenshot_path("debug_screenshot.png")
                    page.screenshot(path=screenshot_path)
                    print(f"Screenshot saved to {screenshot_path}")
                    
                    # Also save the page HTML for debugging
                    html_path = self._get_screenshot_path("debug_page.html")
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(page.content())
                    print(f"HTML saved to {html_path}")
                    return
                
                # Click on the first video to open the player
                print("Clicking on the first video...")
                first_video = page.locator('div[data-e2e="user-post-item"]').first
                first_video.click()
                
                # Wait for the video viewer to open
                self._random_delay(2, 3)
                print("Waiting for video viewer to open...")
                page.wait_for_selector('[data-e2e="browse-video"]', timeout=15000)
                print("Video viewer opened.")
                
                song_titles = set()
                video_count = 0
                
                while video_count < max_videos:
                    try:
                        self._random_delay(0.3, 0.6)
                        video_count += 1
                        
                        title = self._extract_song_title(page)
                        
                        if title and title.strip():
                            title = title.strip()
                            if title not in song_titles:
                                print(f"[{video_count}] Found song: {title}")
                                self.songs.append(title)
                                song_titles.add(title)
                            else:
                                print(f"[{video_count}] Duplicate song: {title}")
                        else:
                            print(f"[{video_count}] Could not find song title for this video.")

                        if not self._navigate_to_next_video(page):
                            break

                    except Exception as e:
                        print(f"Error while processing video {video_count}: {e}")
                        if not self._try_recover_navigation(page):
                            print("Could not recover. Exiting loop.")
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

    def _extract_song_title(self, page):
        """Extract the song title from the current video page."""
        music_selectors = [
            'div[class*="DivMusicText"]',
            'div[class*="MusicText"]',
            'a[data-e2e="browse-music"]',
            'a[data-e2e="video-music"]',
            '[data-e2e="browse-music-name"]',
        ]
        
        for selector in music_selectors:
            try:
                music_element = page.locator(selector).first
                if music_element.is_visible(timeout=2000):
                    title = music_element.inner_text(timeout=3000)
                    if title and title.strip():
                        return title
            except Exception:
                continue
        
        return None

    def _navigate_to_next_video(self, page, retries=3):
        """Navigate to the next video in the profile with retry logic."""
        next_button = page.locator('button[data-e2e="arrow-right"]')
        
        for attempt in range(retries):
            try:
                if next_button.is_visible(timeout=2000):
                    # Check if button is disabled (last video)
                    is_disabled = next_button.get_attribute('disabled')
                    if is_disabled is not None:
                        print("Next button is disabled. Reached the last video.")
                        return False
                    
                    # Button is visible and not disabled - click it
                    next_button.click()
                    self._random_delay(0.5, 1.0)
                    return True
            except Exception:
                pass
            
            # Button not found, wait and retry
            if attempt < retries - 1:
                self._random_delay(1.5, 2.5)
        
        print("Next button not visible after retries. Reached the end.")
        return False

    def _try_recover_navigation(self, page):
        """Try to recover and continue navigation after an error."""
        try:
            next_button = page.locator('button[data-e2e="arrow-right"]')
            if next_button.is_visible(timeout=2000):
                next_button.click()
                self._random_delay(0.5, 1.0)
                return True
        except Exception:
            pass
        return False

    def save_to_json(self, filename="songs.json"):
        """Saves the scraped songs to a JSON file."""
        print(f"Saving {len(self.songs)} songs to {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.songs, f, ensure_ascii=False, indent=4)
        print("Done.")
