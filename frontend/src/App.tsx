import { useState, useEffect } from "react";

// API Configuration
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

// Spotify Configuration
const SPOTIFY_CLIENT_ID = import.meta.env.VITE_SPOTIFY_CLIENT_ID || "";
const SPOTIFY_REDIRECT_URI =
  import.meta.env.VITE_SPOTIFY_REDIRECT_URI ||
  window.location.origin + "/callback";
const SPOTIFY_SCOPES = [
  "user-read-private",
  "user-read-email",
  "playlist-modify-public",
  "playlist-modify-private",
].join(" ");

interface Song {
  song: string | null;
  artist: string | null;
  type: string;
  confidence: string | null;
  tiktok_title: string;
}

interface ScrapeResponse {
  username: string;
  total_videos_scraped: number;
  total_unique_titles: number;
  real_songs_identified: number;
  raw_titles: string[];
  processed_songs: Song[] | null;
  message: string;
}

function App() {
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScrapeResponse | null>(null);
  const [spotifyToken, setSpotifyToken] = useState<string | null>(null);

  // Check for Spotify callback on mount
  useEffect(() => {
    const hash = window.location.hash;
    if (hash) {
      const params = new URLSearchParams(hash.substring(1));
      const token = params.get("access_token");
      if (token) {
        setSpotifyToken(token);
        window.location.hash = "";
      }
    }
  }, []);

  const handleScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/scrape`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username.trim(),
          process_with_ai: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to scrape profile");
      }

      const data: ScrapeResponse = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleSpotifyLogin = () => {
    const authUrl = new URL("https://accounts.spotify.com/authorize");
    authUrl.searchParams.set("client_id", SPOTIFY_CLIENT_ID);
    authUrl.searchParams.set("response_type", "token");
    authUrl.searchParams.set("redirect_uri", SPOTIFY_REDIRECT_URI);
    authUrl.searchParams.set("scope", SPOTIFY_SCOPES);
    window.location.href = authUrl.toString();
  };

  const handleCreatePlaylist = async () => {
    if (!spotifyToken || !result?.processed_songs) return;

    // TODO: Implement Spotify playlist creation
    alert(
      "Playlist creation coming soon! This will search for songs on Spotify and create a playlist.",
    );
  };

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

        {/* Spotify Login */}
        <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">
                Spotify Connection
              </h2>
              <p className="text-gray-400 text-sm">
                {spotifyToken
                  ? "Connected! You can create playlists."
                  : "Connect to create playlists from scraped songs"}
              </p>
            </div>
            {spotifyToken ? (
              <span className="bg-green-500/20 text-green-400 px-4 py-2 rounded-lg">
                ✓ Connected
              </span>
            ) : (
              <button
                onClick={handleSpotifyLogin}
                disabled={!SPOTIFY_CLIENT_ID}
                className="bg-green-500 hover:bg-green-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-semibold transition-colors"
              >
                Connect Spotify
              </button>
            )}
          </div>
          {!SPOTIFY_CLIENT_ID && (
            <p className="text-yellow-400 text-sm mt-2">
              ⚠️ Set VITE_SPOTIFY_CLIENT_ID in .env to enable Spotify
              integration
            </p>
          )}
        </div>

        {/* Scrape Form */}
        <form
          onSubmit={handleScrape}
          className="bg-gray-800/50 backdrop-blur rounded-xl p-6 mb-8"
        >
          <label className="block text-white font-semibold mb-2">
            TikTok Username
          </label>
          <div className="flex gap-4">
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g., mrbeast"
              className="flex-1 bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !username.trim()}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              {loading ? "Scraping..." : "Scrape Songs"}
            </button>
          </div>
          {loading && (
            <p className="text-gray-400 text-sm mt-3">
              ⏳ This may take several minutes depending on the number of
              videos...
            </p>
          )}
        </form>

        {/* Error */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-300 rounded-xl p-4 mb-8">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">
                  Results for @{result.username}
                </h2>
                <p className="text-gray-400">
                  {result.total_unique_titles} audio titles found •{" "}
                  {result.real_songs_identified} real songs identified
                </p>
              </div>
              {spotifyToken &&
                result.processed_songs &&
                result.processed_songs.length > 0 && (
                  <button
                    onClick={handleCreatePlaylist}
                    className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
                  >
                    Create Playlist
                  </button>
                )}
            </div>

            {/* Songs Table */}
            {result.processed_songs && result.processed_songs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="pb-3 text-gray-400 font-semibold">#</th>
                      <th className="pb-3 text-gray-400 font-semibold">Song</th>
                      <th className="pb-3 text-gray-400 font-semibold">
                        Artist
                      </th>
                      <th className="pb-3 text-gray-400 font-semibold">Type</th>
                      <th className="pb-3 text-gray-400 font-semibold">
                        Confidence
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.processed_songs.map((song, index) => (
                      <tr key={index} className="border-b border-gray-700/50">
                        <td className="py-3 text-gray-500">{index + 1}</td>
                        <td className="py-3 text-white font-medium">
                          {song.song || "-"}
                        </td>
                        <td className="py-3 text-gray-300">
                          {song.artist || "-"}
                        </td>
                        <td className="py-3">
                          <span
                            className={`px-2 py-1 rounded text-xs ${
                              song.type === "original"
                                ? "bg-blue-500/20 text-blue-400"
                                : song.type === "remix"
                                  ? "bg-purple-500/20 text-purple-400"
                                  : "bg-gray-500/20 text-gray-400"
                            }`}
                          >
                            {song.type}
                          </span>
                        </td>
                        <td className="py-3">
                          <span
                            className={`px-2 py-1 rounded text-xs ${
                              song.confidence === "high"
                                ? "bg-green-500/20 text-green-400"
                                : song.confidence === "medium"
                                  ? "bg-yellow-500/20 text-yellow-400"
                                  : "bg-red-500/20 text-red-400"
                            }`}
                          >
                            {song.confidence || "unknown"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-400">No identified songs found.</p>
                <p className="text-gray-500 text-sm mt-2">
                  Raw titles scraped: {result.raw_titles.length}
                </p>
              </div>
            )}

            {/* Download Button */}
            <div className="mt-6 pt-6 border-t border-gray-700">
              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(result, null, 2)], {
                    type: "application/json",
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `tiktok-songs-${result.username}.json`;
                  a.click();
                }}
                className="text-purple-400 hover:text-purple-300 transition-colors"
              >
                📥 Download Results as JSON
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
