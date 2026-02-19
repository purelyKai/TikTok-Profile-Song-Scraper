import type { ScrapeResponse } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

export async function scrapeTikTokProfile(
  username: string,
): Promise<ScrapeResponse> {
  const response = await fetch(`${API_URL}/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username: username.trim(),
      process_with_ai: true,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to scrape profile");
  }

  return response.json();
}
