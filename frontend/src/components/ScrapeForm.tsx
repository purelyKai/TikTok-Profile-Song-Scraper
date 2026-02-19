import { useState } from "react";

interface ScrapeFormProps {
  onScrape: (username: string) => Promise<void>;
  isLoading: boolean;
  disabled: boolean;
}

export function ScrapeForm({ onScrape, isLoading, disabled }: ScrapeFormProps) {
  const [username, setUsername] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || disabled) return;
    await onScrape(username.trim());
  };

  return (
    <form
      onSubmit={handleSubmit}
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
          className="flex-1 bg-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
          disabled={isLoading || disabled}
        />
        <button
          type="submit"
          disabled={isLoading || !username.trim() || disabled}
          className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-8 py-3 rounded-lg font-semibold transition-colors"
        >
          {isLoading ? "Scraping..." : "Scrape Songs"}
        </button>
      </div>
      {disabled && (
        <p className="text-yellow-400 text-sm mt-3">
          ⚠️ Please sign in with Spotify first to scrape songs
        </p>
      )}
      {isLoading && (
        <p className="text-gray-400 text-sm mt-3">
          ⏳ This may take several minutes depending on the number of videos...
        </p>
      )}
    </form>
  );
}
