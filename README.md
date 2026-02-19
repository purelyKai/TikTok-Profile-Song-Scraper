# TikTok Profile Song Scraper

Extract songs from any TikTok profile and create a Spotify playlist.

## Project Structure

```
├── backend/                     # FastAPI + Playwright backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app + routes
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py       # Pydantic request/response models
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── scraper.py       # TikTok scraping logic
│   │       └── processor.py     # Gemini AI song processing
│   ├── cli.py                   # Command-line interface
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── output/                  # Scraped data output
│
├── frontend/                    # React + Vite frontend
│   ├── src/
│   │   └── App.tsx              # Main React component
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
│
├── docker-compose.yml           # Local development
├── .env.example
├── README.md
└── LICENSE
```

## Quick Start

### Backend (API Server)

```bash
# With Docker (recommended)
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
docker-compose up --build

# API available at http://localhost:8080
# API docs at http://localhost:8080/docs
```

### Frontend (React App)

```bash
cd frontend
cp .env.example .env
# Edit .env with your API URL and Spotify credentials
npm install
npm run dev

# Frontend available at http://localhost:5173
```

### CLI (Command Line)

```bash
cd backend
pip install -r requirements.txt
playwright install chromium

# Scrape a profile
python cli.py --profile mrbeast

# Options:
python cli.py --scrape-only     # Skip AI processing
python cli.py --process-only    # Process existing raw_songs.json
```

## Environment Variables

### Backend (.env)

```env
GEMINI_API_KEY=your_gemini_api_key_here
FRONTEND_URL=http://localhost:5173
```

### Frontend (frontend/.env)

```env
VITE_API_URL=http://localhost:8080
VITE_SPOTIFY_CLIENT_ID=your_spotify_client_id
VITE_SPOTIFY_REDIRECT_URI=http://localhost:5173/callback
```

## Deployment

### Backend → Google Cloud Run

The backend uses Playwright with Chromium, which requires significant resources. Scraping a large profile can take up to 20 minutes.

```bash
cd backend
gcloud run deploy tiktok-scraper-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 1200 \
  --memory 4Gi \
  --cpu 4 \
  --concurrency 1 \
  --min-instances 0 \
  --max-instances 2 \
  --set-env-vars "HEADLESS=true,GEMINI_API_KEY=YOUR_ACTUAL_KEY,FRONTEND_URL=https://your-frontend.vercel.app"
```

**Resource Settings Explained:**

| Setting           | Value | Why                                                     |
| ----------------- | ----- | ------------------------------------------------------- |
| `--timeout`       | 1200  | 20 minutes max for large profiles (max allowed: 3600)   |
| `--memory`        | 4Gi   | Chromium needs ~2-3GB, extra headroom for stability     |
| `--cpu`           | 4     | Browser rendering is CPU-intensive                      |
| `--concurrency`   | 1     | Each request gets dedicated resources (browser-heavy)   |
| `--min-instances` | 0     | Scale to zero when idle (cost savings, ~30s cold start) |
| `--max-instances` | 2     | Limit concurrent containers to control costs            |

**Cost Note:** You only pay while processing requests (~$0.00002400/vCPU-second, ~$0.00000250/GiB-second).

### Frontend → Vercel

```bash
cd frontend
vercel --prod
```

Set environment variables in Vercel dashboard:

- `VITE_API_URL` → Your Cloud Run URL
- `VITE_SPOTIFY_CLIENT_ID` → From Spotify Developer Dashboard
- `VITE_SPOTIFY_REDIRECT_URI` → `https://your-app.vercel.app/callback`

## API Endpoints

| Method | Endpoint | Description                |
| ------ | -------- | -------------------------- |
| GET    | /        | Health check               |
| GET    | /health  | Health check for Cloud Run |
| POST   | /scrape  | Scrape a TikTok profile    |

### POST /scrape

Request:

```json
{
  "username": "mrbeast",
  "process_with_ai": true
}
```

Response:

```json
{
  "username": "mrbeast",
  "total_videos_scraped": 100,
  "total_unique_titles": 85,
  "real_songs_identified": 42,
  "raw_titles": ["song1", "song2"],
  "processed_songs": [
    {
      "song": "Song Title",
      "artist": "Artist Name",
      "type": "original",
      "confidence": "high",
      "tiktok_title": "original tiktok audio title"
    }
  ],
  "message": "Successfully scraped 85 unique audio titles"
}
```

## License

MIT License - see [LICENSE](LICENSE) for details
