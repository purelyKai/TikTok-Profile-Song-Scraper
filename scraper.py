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

    def _random_delay(self, min_sec=1.5, max_sec=3.5):
        """
        Add a random delay to mimic human behavior.
        
        Args:
            min_sec (float): Minimum delay in seconds.
            max_sec (float): Maximum delay in seconds.
        """
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _setup_browser(self, playwright):
        """
        Sets up a browser with stealth settings to avoid bot detection.
        
        Args:
            playwright: Playwright instance.
            
        Returns:
            tuple: (browser, context, page) objects.
        """
        # Check for headless mode (for Docker/CI environments)
        headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        
        if headless:
            print("Running in headless mode (Docker/CI environment)")
        
        # Launch browser with specific args to avoid detection
        browser = playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--disable-browser-side-navigation',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        
        # Create context with realistic browser fingerprint
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/Los_Angeles',
            geolocation={'latitude': 34.0522, 'longitude': -118.2437},
            permissions=['geolocation'],
            color_scheme='light',
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
        )
        
        # Create page and apply stealth
        page = context.new_page()
        Stealth().apply_stealth_sync(page)
        
        return browser, context, page

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
                page.goto(self.url, wait_until='networkidle', timeout=60000)
                
                # Random delay to mimic human behavior
                self._random_delay(2, 4)
                
                # Check if we hit an error page
                if "Something went wrong" in page.content():
                    print("TikTok blocked the request. Trying to refresh...")
                    self._random_delay(3, 5)
                    page.reload(wait_until='networkidle', timeout=60000)
                    self._random_delay(2, 4)
                
                # Wait for the video grid to load
                print("Waiting for the video grid to load...")
                try:
                    page.wait_for_selector('div[data-e2e="user-post-item"]', timeout=30000)
                except Exception:
                    print("Could not find video grid. Page content may be blocked.")
                    print("Taking screenshot for debugging...")
                    page.screenshot(path="debug_screenshot.png")
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
                        self._random_delay(0.3, 0.6)  # Reduced delay for faster scraping
                        video_count += 1
                        
                        # Try multiple selectors for the music/song title
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

                        # Check if we can navigate to the next video
                        if not self._navigate_to_next_video(page):
                            break

                    except Exception as e:
                        print(f"Error while processing video {video_count}: {e}")
                        # Try to recover and continue
                        if not self._try_recover_navigation(page):
                            print("Could not recover. Exiting loop.")
                            break
                
                print(f"\nScraping complete! Found {len(self.songs)} unique songs from {video_count} videos.")

            except Exception as e:
                print(f"An error occurred: {e}")
                try:
                    page.screenshot(path="error_screenshot.png")
                    print("Screenshot saved to error_screenshot.png")
                except Exception:
                    pass
            finally:
                context.close()
                browser.close()
                print("Browser closed.")

    def _extract_song_title(self, page):
        """
        Extract the song title from the current video page.
        
        Args:
            page: Playwright page object.
            
        Returns:
            str or None: The song title if found, None otherwise.
        """
        # Selectors in order of preference
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

    def _navigate_to_next_video(self, page):
        """
        Navigate to the next video in the profile.
        
        Args:
            page: Playwright page object.
            
        Returns:
            bool: True if navigation was successful, False if at the end.
        """
        next_button = page.locator('button[data-e2e="arrow-right"]')
        
        if not next_button.is_visible(timeout=2000):
            print("Next button not visible. Reached the end.")
            return False
        
        # Check if button is disabled (last video)
        is_disabled = next_button.get_attribute('disabled')
        if is_disabled is not None:
            print("Next button is disabled. Reached the last video.")
            return False
        
        # Click the "next" button
        next_button.click()
        self._random_delay(0.5, 1.0)
        return True

    def _try_recover_navigation(self, page):
        """
        Try to recover and continue navigation after an error.
        
        Args:
            page: Playwright page object.
            
        Returns:
            bool: True if recovery was successful.
        """
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
        """
        Saves the scraped songs to a JSON file.
        
        Args:
            filename (str): The output filename.
        """
        print(f"Saving {len(self.songs)} songs to {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.songs, f, ensure_ascii=False, indent=4)
        print("Done.")
