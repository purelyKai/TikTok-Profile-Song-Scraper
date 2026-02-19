import type { SpotifyUser } from "../types";

interface SpotifyAuthProps {
  user: SpotifyUser | null;
  isConfigured: boolean;
  onLogin: () => void;
  onLogout: () => void;
}

export function SpotifyAuth({
  user,
  isConfigured,
  onLogin,
  onLogout,
}: SpotifyAuthProps) {
  return (
    <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6 mb-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {user?.images?.[0]?.url && (
            <img
              src={user.images[0].url}
              alt={user.display_name}
              className="w-12 h-12 rounded-full"
            />
          )}
          <div>
            <h2 className="text-xl font-semibold text-white">
              {user ? `Welcome, ${user.display_name}!` : "Spotify Connection"}
            </h2>
            <p className="text-gray-400 text-sm">
              {user
                ? "You can scrape TikTok songs and create playlists."
                : "Sign in with Spotify to start scraping songs"}
            </p>
          </div>
        </div>
        {user ? (
          <button
            onClick={onLogout}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Sign Out
          </button>
        ) : (
          <button
            onClick={onLogin}
            disabled={!isConfigured}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-semibold transition-colors"
          >
            Sign in with Spotify
          </button>
        )}
      </div>
      {!isConfigured && (
        <p className="text-yellow-400 text-sm mt-2">
          ⚠️ Set VITE_SPOTIFY_CLIENT_ID in .env to enable Spotify integration
        </p>
      )}
    </div>
  );
}
