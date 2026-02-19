import { useState, useEffect } from "react";
import { useSpotify } from "./hooks/useSpotify";
import { scrapeTikTokProfile } from "./services/api";
import { SpotifyAuth } from "./components/SpotifyAuth";
import { ScrapeForm } from "./components/ScrapeForm";
import { SongList } from "./components/SongList";
import type { ScrapeResponse } from "./types";

const STORAGE_KEY = "tiktok_scrape_result";

function App() {
  const spotify = useSpotify();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScrapeResponse | null>(null);

  // Load persisted result from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setResult(JSON.parse(stored));
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  // Persist result to localStorage whenever it changes
  useEffect(() => {
    if (result) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
    }
  }, [result]);

  const handleScrape = async (username: string) => {
    setLoading(true);
    setError(null);

    try {
      const data = await scrapeTikTokProfile(username);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setResult(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  // Show loading while checking Spotify auth
  if (spotify.isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">
            🎵 TikTok Song Scraper
          </h1>
          <p className="text-gray-300 text-lg">
            Extract songs from any TikTok profile and create a Spotify playlist
          </p>
        </div>

        {/* Spotify Auth */}
        <SpotifyAuth
          user={spotify.user}
          isConfigured={spotify.isConfigured}
          onLogin={spotify.login}
          onLogout={spotify.logout}
        />

        {/* Scrape Form - disabled if not logged in */}
        <ScrapeForm
          onScrape={handleScrape}
          isLoading={loading}
          disabled={!spotify.user}
        />

        {/* Error */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-300 rounded-xl p-4 mb-8">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <SongList
            result={result}
            isLoggedIn={!!spotify.user}
            onCreatePlaylist={spotify.createPlaylist}
            onClear={handleClear}
          />
        )}
      </div>
    </div>
  );
}

export default App;
