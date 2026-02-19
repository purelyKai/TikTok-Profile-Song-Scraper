// Song types
export interface Song {
  song: string | null;
  artist: string | null;
  type: string;
  confidence: string | null;
  tiktok_title: string;
}

export interface ScrapeResponse {
  username: string;
  total_videos_scraped: number;
  total_unique_titles: number;
  real_songs_identified: number;
  raw_titles: string[];
  processed_songs: Song[] | null;
  message: string;
}

// Spotify types
export interface SpotifyUser {
  id: string;
  display_name: string;
  email: string;
  images: { url: string }[];
}

export interface SpotifyTrack {
  id: string;
  name: string;
  artists: { name: string }[];
  uri: string;
}

export interface SpotifySearchResult {
  tracks: {
    items: SpotifyTrack[];
  };
}

export interface SpotifyPlaylist {
  id: string;
  name: string;
  external_urls: {
    spotify: string;
  };
}
