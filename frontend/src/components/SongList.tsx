import { useState } from "react";
import type { ScrapeResponse, Song, SpotifyPlaylist } from "../types";

interface SongListProps {
  result: ScrapeResponse;
  isLoggedIn: boolean;
  onCreatePlaylist: (
    name: string,
    songs: Song[],
    onProgress?: (current: number, total: number) => void,
  ) => Promise<SpotifyPlaylist | null>;
  onClear: () => void;
}

export function SongList({
  result,
  isLoggedIn,
  onCreatePlaylist,
  onClear,
}: SongListProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [createdPlaylist, setCreatedPlaylist] =
    useState<SpotifyPlaylist | null>(null);

  const handleCreatePlaylist = async () => {
    if (!result.processed_songs) return;

    setIsCreating(true);
    setProgress({ current: 0, total: result.processed_songs.length });

    const playlist = await onCreatePlaylist(
      `TikTok Songs - @${result.username}`,
      result.processed_songs,
      (current, total) => setProgress({ current, total }),
    );

    setIsCreating(false);

    if (playlist) {
      setCreatedPlaylist(playlist);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tiktok-songs-${result.username}.json`;
    a.click();
  };

  return (
    <div className="bg-gray-800/50 backdrop-blur rounded-xl p-6">
      {/* Header */}
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
        <div className="flex gap-3">
          {isLoggedIn &&
            result.processed_songs &&
            result.processed_songs.length > 0 &&
            !createdPlaylist && (
              <button
                onClick={handleCreatePlaylist}
                disabled={isCreating}
                className="bg-green-500 hover:bg-green-600 disabled:bg-green-700 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
              >
                {isCreating
                  ? `Creating... (${progress.current}/${progress.total})`
                  : "Create Playlist"}
              </button>
            )}
          <button
            onClick={onClear}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Playlist Created Success */}
      {createdPlaylist && (
        <div className="bg-green-500/20 border border-green-500 rounded-lg p-4 mb-6">
          <p className="text-green-300 font-semibold">
            ✓ Playlist created successfully!
          </p>
          <a
            href={createdPlaylist.external_urls.spotify}
            target="_blank"
            rel="noopener noreferrer"
            className="text-green-400 hover:text-green-300 underline"
          >
            Open "{createdPlaylist.name}" in Spotify →
          </a>
        </div>
      )}

      {/* Songs Table */}
      {result.processed_songs && result.processed_songs.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="pb-3 text-gray-400 font-semibold">#</th>
                <th className="pb-3 text-gray-400 font-semibold">Song</th>
                <th className="pb-3 text-gray-400 font-semibold">Artist</th>
                <th className="pb-3 text-gray-400 font-semibold">Type</th>
                <th className="pb-3 text-gray-400 font-semibold">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {result.processed_songs.map((song, index) => (
                <tr key={index} className="border-b border-gray-700/50">
                  <td className="py-3 text-gray-500">{index + 1}</td>
                  <td className="py-3 text-white font-medium">
                    {song.song || "-"}
                  </td>
                  <td className="py-3 text-gray-300">{song.artist || "-"}</td>
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
          onClick={handleDownload}
          className="text-purple-400 hover:text-purple-300 transition-colors"
        >
          📥 Download Results as JSON
        </button>
      </div>
    </div>
  );
}
