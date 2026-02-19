# TikTok Profile Song Scraper

Scrape audio/song titles from any TikTok user's profile and optionally use Gemini AI to identify real songs from the raw audio titles.

## Features

- **Stealth Scraping**: Uses Playwright with stealth capabilities to bypass TikTok's bot detection
- **AI Song Identification**: Integrates with Google's Gemini AI to identify real songs from TikTok audio titles
- **Modular Design**: Clean separation of concerns with dedicated scraper and processor modules
- **Flexible CLI**: Run full pipeline, scrape-only, or process-only modes

## Project Structure

```
├── main.py           # Main entry point with CLI
├── scraper.py        # TikTokScraper class for web scraping
├── processor.py      # SongProcessor class for AI processing
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment configuration
└── .env              # Your environment configuration (create this)
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/purelyKai/TikTok-Profile-Song-Scraper.git
cd TikTok-Profile-Song-Scraper
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:

```bash
python -m playwright install chromium
```

4. Create your `.env` file:

```bash
cp .env.example .env
```

5. Edit `.env` with your configuration:

```env
PROFILE=tiktok_username_to_scrape
GEMINI_API_KEY=your_gemini_api_key  # Optional, for AI processing
```

## Usage

### Full Pipeline (Scrape + AI Processing)

```bash
python main.py
```

### Scrape Only (No AI Processing)

```bash
python main.py --scrape-only
```

### Process Existing Data with AI

```bash
python main.py --process-only
```

### Specify Profile via CLI

```bash
python main.py --profile username
```

## Output Files

- **`raw_songs.json`**: Raw TikTok audio titles as scraped
- **`processed_songs.json`**: Full AI analysis results with metadata
- **`songs.json`**: Clean list of identified real songs

## Docker Usage

### Using Docker Compose (Recommended)

1. Make sure your `.env` file is configured
2. Run the scraper:

```bash
docker-compose up --build
```

3. Results will be saved to the `./output` directory

### Using Docker Directly

Build the image:

```bash
docker build -t tiktok-scraper .
```

Run the container:

```bash
docker run --rm \
  -e PROFILE=tiktok_username \
  -e GEMINI_API_KEY=your_api_key \
  -v $(pwd)/output:/app/output \
  tiktok-scraper
```

### Docker Environment Variables

| Variable         | Description                                              | Required |
| ---------------- | -------------------------------------------------------- | -------- |
| `PROFILE`        | TikTok username to scrape                                | Yes      |
| `GEMINI_API_KEY` | Gemini API key for AI processing                         | No       |
| `HEADLESS`       | Run browser in headless mode (default: `true` in Docker) | No       |

## Getting a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key (free tier available)
3. Add it to your `.env` file

## How It Works

1. **Scraping**: The scraper navigates to the TikTok profile, opens each video, and extracts the audio title using Playwright with stealth settings to avoid detection.

2. **AI Processing**: The processor sends batches of audio titles to Gemini AI, which:
   - Identifies if each title is a real song or user-created audio
   - Extracts the actual song name and artist
   - Notes if it's a remix, cover, or mashup
   - Provides confidence levels

## Requirements

- Python 3.8+
- Chromium browser (installed via Playwright)
- Internet connection
- (Optional) Gemini API key for AI processing

## Dependencies

- `playwright` - Browser automation
- `playwright-stealth` - Stealth capabilities to avoid detection
- `python-dotenv` - Environment variable management
- `google-genai` - Gemini AI integration

## License

MIT License - see [LICENSE](LICENSE) for details
