import { useState, useEffect, useCallback } from "react";
import type {
  SpotifyUser,
  SpotifyTrack,
  SpotifyPlaylist,
  Song,
} from "../types";

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

// Storage keys
const TOKEN_KEY = "spotify_access_token";
const TOKEN_EXPIRY_KEY = "spotify_token_expiry";
const VERIFIER_KEY = "spotify_code_verifier";

// PKCE Helpers
function generateRandomString(length: number): string {
  const possible =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  const values = crypto.getRandomValues(new Uint8Array(length));
  return values.reduce((acc, x) => acc + possible[x % possible.length], "");
}

async function sha256(plain: string): Promise<ArrayBuffer> {
  const encoder = new TextEncoder();
  const data = encoder.encode(plain);
  return window.crypto.subtle.digest("SHA-256", data);
}

function base64urlencode(input: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(input)))
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
}

async function generateCodeChallenge(codeVerifier: string): Promise<string> {
  const hashed = await sha256(codeVerifier);
  return base64urlencode(hashed);
}

export function useSpotify() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<SpotifyUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if token is valid
  const isTokenValid = useCallback(() => {
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
    if (!expiry) return false;
    return Date.now() < parseInt(expiry);
  }, []);

  // Initialize - check for existing token or callback
  useEffect(() => {
    const initAuth = async () => {
      // Check for callback code
      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");
      const storedVerifier = localStorage.getItem(VERIFIER_KEY);

      if (code && storedVerifier) {
        await exchangeCodeForToken(code, storedVerifier);
        window.history.replaceState(
          {},
          document.title,
          window.location.pathname,
        );
      } else {
        // Check for existing valid token
        const storedToken = localStorage.getItem(TOKEN_KEY);
        if (storedToken && isTokenValid()) {
          setToken(storedToken);
          await fetchUser(storedToken);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, [isTokenValid]);

  // Exchange auth code for token
  const exchangeCodeForToken = async (code: string, codeVerifier: string) => {
    try {
      const response = await fetch("https://accounts.spotify.com/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          client_id: SPOTIFY_CLIENT_ID,
          grant_type: "authorization_code",
          code,
          redirect_uri: SPOTIFY_REDIRECT_URI,
          code_verifier: codeVerifier,
        }),
      });

      const data = await response.json();

      if (data.access_token) {
        const expiresAt = Date.now() + data.expires_in * 1000;
        localStorage.setItem(TOKEN_KEY, data.access_token);
        localStorage.setItem(TOKEN_EXPIRY_KEY, expiresAt.toString());
        localStorage.removeItem(VERIFIER_KEY);
        setToken(data.access_token);
        await fetchUser(data.access_token);
      }
    } catch (err) {
      console.error("Token exchange error:", err);
    }
  };

  // Fetch user profile
  const fetchUser = async (accessToken: string) => {
    try {
      const response = await fetch("https://api.spotify.com/v1/me", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (err) {
      console.error("Failed to fetch user:", err);
    }
  };

  // Login
  const login = async () => {
    const codeVerifier = generateRandomString(64);
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    localStorage.setItem(VERIFIER_KEY, codeVerifier);

    const authUrl = new URL("https://accounts.spotify.com/authorize");
    authUrl.searchParams.set("client_id", SPOTIFY_CLIENT_ID);
    authUrl.searchParams.set("response_type", "code");
    authUrl.searchParams.set("redirect_uri", SPOTIFY_REDIRECT_URI);
    authUrl.searchParams.set("scope", SPOTIFY_SCOPES);
    authUrl.searchParams.set("code_challenge_method", "S256");
    authUrl.searchParams.set("code_challenge", codeChallenge);

    window.location.href = authUrl.toString();
  };

  // Logout
  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    setToken(null);
    setUser(null);
  };

  // Search for a track on Spotify
  const searchTrack = async (
    songName: string,
    artistName: string,
  ): Promise<SpotifyTrack | null> => {
    if (!token) return null;

    try {
      // Build search query - combine song and artist for better results
      const query = artistName ? `${songName} ${artistName}` : songName;

      const url = new URL("https://api.spotify.com/v1/search");
      url.searchParams.set("q", query);
      url.searchParams.set("type", "track");
      url.searchParams.set("limit", "1");

      const response = await fetch(url.toString(), {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        console.error("Search failed:", response.status, await response.text());
        return null;
      }

      const data = await response.json();
      const track = data.tracks?.items?.[0] || null;

      if (track) {
        console.log(`Found: "${track.name}" by ${track.artists[0]?.name}`);
      } else {
        console.log(`Not found: "${songName}" by "${artistName}"`);
      }

      return track;
    } catch (err) {
      console.error("Search error:", err);
      return null;
    }
  };

  // Create playlist and add tracks
  const createPlaylist = async (
    name: string,
    songs: Song[],
    onProgress?: (current: number, total: number) => void,
  ): Promise<SpotifyPlaylist | null> => {
    if (!token || !user) {
      console.error("No token or user for playlist creation");
      return null;
    }

    try {
      // Step 1: Create empty playlist using /me/playlists endpoint
      console.log(`Creating playlist "${name}"...`);
      const createResponse = await fetch(
        "https://api.spotify.com/v1/me/playlists",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name,
            description: "Created with TikTok Song Scraper",
            public: false,
          }),
        },
      );

      if (!createResponse.ok) {
        const errorText = await createResponse.text();
        console.error(
          "Failed to create playlist:",
          createResponse.status,
          errorText,
        );
        return null;
      }

      const playlist: SpotifyPlaylist = await createResponse.json();
      console.log(`Playlist created: ${playlist.id}`);

      // Step 2: Search for each song and collect URIs
      const trackUris: string[] = [];
      const songsToSearch = songs.filter((s) => s.song);
      console.log(`Searching for ${songsToSearch.length} songs...`);

      for (let i = 0; i < songsToSearch.length; i++) {
        const song = songsToSearch[i];
        if (song.song) {
          const track = await searchTrack(song.song, song.artist || "");
          if (track?.uri) {
            trackUris.push(track.uri);
          }
          onProgress?.(i + 1, songsToSearch.length);
          // Small delay to avoid rate limiting
          await new Promise((r) => setTimeout(r, 50));
        }
      }

      console.log(`Found ${trackUris.length} tracks to add`);

      // Step 3: Add tracks to playlist in batches of 100 using /items endpoint
      if (trackUris.length > 0) {
        for (let i = 0; i < trackUris.length; i += 100) {
          const batch = trackUris.slice(i, i + 100);
          console.log(`Adding batch of ${batch.length} tracks...`);

          const addResponse = await fetch(
            `https://api.spotify.com/v1/playlists/${playlist.id}/items`,
            {
              method: "POST",
              headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ uris: batch }),
            },
          );

          if (!addResponse.ok) {
            const errorText = await addResponse.text();
            console.error(
              "Failed to add tracks:",
              addResponse.status,
              errorText,
            );
          } else {
            console.log(`Added ${batch.length} tracks successfully`);
          }
        }
      }

      return playlist;
    } catch (err) {
      console.error("Playlist creation error:", err);
      return null;
    }
  };

  return {
    token,
    user,
    isLoading,
    isConfigured: !!SPOTIFY_CLIENT_ID,
    login,
    logout,
    createPlaylist,
  };
}
