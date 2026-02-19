"""
Song Processor Module

This module contains the SongProcessor class that uses Gemini AI
to identify real songs from raw TikTok audio titles.
"""

import json
import time
from google import genai


class SongProcessor:
    """
    Uses Gemini AI to process raw TikTok audio titles and identify real songs.
    """
    
    def __init__(self, api_key, model_name='gemini-2.0-flash'):
        """
        Initialize the processor with a Gemini API key.
        
        Args:
            api_key (str): Gemini API key.
            model_name (str): The Gemini model to use.
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        
    def process_songs(self, raw_titles, batch_size=20):
        """
        Process a list of raw TikTok audio titles to identify real songs.
        
        Args:
            raw_titles (list): List of raw audio titles from TikTok.
            batch_size (int): Number of titles to process per API call.
            
        Returns:
            list: List of identified songs with their details.
        """
        all_results = []
        
        # Process in batches to avoid token limits
        for i in range(0, len(raw_titles), batch_size):
            batch = raw_titles[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(raw_titles) + batch_size - 1) // batch_size
            
            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} titles)...")
            
            try:
                results = self._process_batch(batch)
                all_results.extend(results)
                real_count = len([r for r in results if r.get('is_real_song')])
                print(f"  Found {real_count} real songs in this batch.")
                
                # Small delay between batches to avoid rate limiting
                if i + batch_size < len(raw_titles):
                    time.sleep(1)
                    
            except Exception as e:
                print(f"  Error processing batch: {e}")
                # Add unprocessed items as unknown
                for title in batch:
                    all_results.append({
                        "original_title": title,
                        "is_real_song": None,
                        "error": str(e)
                    })
        
        return all_results
    
    def _process_batch(self, titles):
        """
        Process a batch of titles using Gemini.
        
        Args:
            titles (list): List of audio titles to process.
            
        Returns:
            list: Processed results for each title.
        """
        titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
        
        prompt = f"""Analyze these TikTok audio titles and identify which ones are real songs (not user-created original sounds).

For each title, determine:
1. Is it a real song? (not "original sound" by a random user)
2. If it's a real song, provide the correct song name and artist
3. If the title contains lyrics, try to identify the actual song
4. Note if it's a remix, cover, or mashup

TikTok Audio Titles:
{titles_text}

Respond in JSON format as a list of objects:
[
  {{
    "original_title": "the original title",
    "is_real_song": true/false,
    "song_name": "Actual Song Name" or null,
    "artist": "Artist Name" or null,
    "is_remix": true/false,
    "is_cover": true/false,
    "confidence": "high/medium/low",
    "notes": "any relevant notes"
  }}
]

Important rules:
- "original sound - [username]" entries are NOT real songs (is_real_song: false)
- Songs with real artist names in the title ARE real songs
- If you recognize lyrics, identify the actual song
- Be somewhat liberal - if you think it could be a real song, mark it as such, but use confidence levels to indicate uncertainty
- Return ONLY valid JSON, no other text"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        response_text = response.text.strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first and last lines (```json and ```)
            response_text = "\n".join(lines[1:-1])
        
        try:
            results = json.loads(response_text)
            return results
        except json.JSONDecodeError as e:
            print(f"  Warning: Could not parse JSON response: {e}")
            print(f"  Response was: {response_text[:500]}...")
            # Return basic structure for each title
            return [{"original_title": t, "is_real_song": None, "parse_error": True} for t in titles]
    
    def get_real_songs_only(self, processed_results):
        """
        Filter processed results to only include confirmed real songs.
        
        Args:
            processed_results (list): Results from process_songs().
            
        Returns:
            list: Only the entries that are confirmed real songs.
        """
        return [
            r for r in processed_results 
            if r.get("is_real_song") == True and r.get("song_name")
        ]
    
    def format_song_list(self, processed_results, include_originals=False):
        """
        Format the processed results into a clean song list.
        
        Args:
            processed_results (list): Results from process_songs().
            include_originals (bool): Whether to include non-song entries.
            
        Returns:
            list: Formatted song entries.
        """
        formatted = []
        
        for r in processed_results:
            if r.get("is_real_song"):
                entry = {
                    "song": r.get("song_name", r.get("original_title")),
                    "artist": r.get("artist", "Unknown"),
                }
                if r.get("is_remix"):
                    entry["type"] = "remix"
                elif r.get("is_cover"):
                    entry["type"] = "cover"
                else:
                    entry["type"] = "original"
                    
                entry["confidence"] = r.get("confidence", "unknown")
                entry["tiktok_title"] = r.get("original_title")
                formatted.append(entry)
                
            elif include_originals:
                formatted.append({
                    "song": None,
                    "artist": None,
                    "type": "user_original",
                    "tiktok_title": r.get("original_title")
                })
        
        return formatted

    def save_results(self, processed_results, filename="processed_songs.json"):
        """
        Save processed results to a JSON file.
        
        Args:
            processed_results (list): Results from process_songs().
            filename (str): Output filename.
        """
        print(f"Saving processed results to {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(processed_results, f, ensure_ascii=False, indent=4)
        print("Done.")

    def save_formatted_songs(self, processed_results, filename="songs.json"):
        """
        Save formatted real songs to a JSON file.
        
        Args:
            processed_results (list): Results from process_songs().
            filename (str): Output filename.
        """
        real_songs = self.format_song_list(processed_results)
        print(f"Saving {len(real_songs)} identified real songs to {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(real_songs, f, ensure_ascii=False, indent=4)
        print("Done.")
        return real_songs
