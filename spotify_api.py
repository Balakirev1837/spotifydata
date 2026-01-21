"""
Spotify API integration for fetching artist genres.

This module handles authentication and genre fetching from the Spotify Web API.
Credentials should be set via environment variables:
  - SPOTIFY_CLIENT_ID
  - SPOTIFY_CLIENT_SECRET

The module gracefully handles missing credentials and caches results locally.
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# File paths
CACHE_DIR = Path(__file__).parent / ".cache"
GENRE_CACHE_FILE = CACHE_DIR / "artist_genres.json"
TOKEN_CACHE_FILE = CACHE_DIR / "spotify_token.json"

# API endpoints
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


def is_api_available() -> bool:
    """Check if Spotify API credentials are configured."""
    if not REQUESTS_AVAILABLE:
        return False
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    return bool(client_id and client_secret)


def get_api_status() -> dict:
    """Get current API configuration status."""
    return {
        "requests_installed": REQUESTS_AVAILABLE,
        "credentials_configured": is_api_available(),
        "client_id_set": bool(os.environ.get("SPOTIFY_CLIENT_ID")),
        "client_secret_set": bool(os.environ.get("SPOTIFY_CLIENT_SECRET")),
        "cache_exists": GENRE_CACHE_FILE.exists(),
        "cached_artists": len(load_genre_cache()) if GENRE_CACHE_FILE.exists() else 0,
    }


def _ensure_cache_dir():
    """Ensure cache directory exists."""
    CACHE_DIR.mkdir(exist_ok=True)


def load_genre_cache() -> dict[str, list[str]]:
    """Load cached artist genres from disk."""
    if not GENRE_CACHE_FILE.exists():
        return {}
    try:
        with open(GENRE_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_genre_cache(cache: dict[str, list[str]]):
    """Save artist genres cache to disk."""
    _ensure_cache_dir()
    with open(GENRE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def _load_token_cache() -> dict | None:
    """Load cached access token."""
    if not TOKEN_CACHE_FILE.exists():
        return None
    try:
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Check if token is expired
            expires_at = datetime.fromisoformat(data.get("expires_at", "2000-01-01"))
            if datetime.now() < expires_at:
                return data
    except (json.JSONDecodeError, IOError, ValueError):
        pass
    return None


def _save_token_cache(token: str, expires_in: int):
    """Save access token to cache."""
    _ensure_cache_dir()
    expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # 1 min buffer
    with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "access_token": token,
            "expires_at": expires_at.isoformat(),
        }, f)


def get_access_token() -> str | None:
    """
    Get access token using client credentials flow.
    Returns None if credentials not configured or request fails.
    """
    if not is_api_available():
        return None

    # Check cache first
    cached = _load_token_cache()
    if cached:
        return cached["access_token"]

    # Request new token
    try:
        response = requests.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": os.environ["SPOTIFY_CLIENT_ID"],
                "client_secret": os.environ["SPOTIFY_CLIENT_SECRET"],
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        _save_token_cache(token, expires_in)
        return token
    except Exception as e:
        print(f"Failed to get Spotify access token: {e}")
        return None


def fetch_artists_genres(artist_ids: list[str], token: str) -> dict[str, list[str]]:
    """
    Fetch genres for multiple artists from Spotify API.
    Batches requests (max 50 per call) and handles rate limiting.

    Returns dict mapping artist_id -> list of genres.
    """
    if not artist_ids or not token:
        return {}

    results = {}
    # Deduplicate and filter empty IDs
    unique_ids = list(set(aid for aid in artist_ids if aid))

    # Batch in chunks of 50
    for i in range(0, len(unique_ids), 50):
        batch = unique_ids[i:i + 50]

        try:
            response = requests.get(
                f"{SPOTIFY_API_BASE}/artists",
                params={"ids": ",".join(batch)},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                # Retry this batch
                response = requests.get(
                    f"{SPOTIFY_API_BASE}/artists",
                    params={"ids": ",".join(batch)},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )

            response.raise_for_status()

            for artist in response.json().get("artists", []):
                if artist:
                    results[artist["id"]] = artist.get("genres", [])

        except Exception as e:
            print(f"Error fetching artist batch: {e}")
            continue

        # Small delay between batches to be nice to the API
        if i + 50 < len(unique_ids):
            time.sleep(0.1)

    return results


def fetch_track_artists(track_ids: list[str], token: str) -> dict[str, list[dict]]:
    """
    Fetch artist info for tracks from Spotify API.
    Returns dict mapping track_id -> list of {id, name} dicts.
    """
    if not track_ids or not token:
        return {}

    results = {}
    unique_ids = list(set(tid for tid in track_ids if tid))

    # Batch in chunks of 50
    for i in range(0, len(unique_ids), 50):
        batch = unique_ids[i:i + 50]

        try:
            response = requests.get(
                f"{SPOTIFY_API_BASE}/tracks",
                params={"ids": ",".join(batch)},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                time.sleep(retry_after)
                response = requests.get(
                    f"{SPOTIFY_API_BASE}/tracks",
                    params={"ids": ",".join(batch)},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )

            response.raise_for_status()

            for track in response.json().get("tracks", []):
                if track:
                    artists = [
                        {"id": a["id"], "name": a["name"]}
                        for a in track.get("artists", [])
                    ]
                    results[track["id"]] = artists

        except Exception as e:
            print(f"Error fetching track batch: {e}")
            continue

        if i + 50 < len(unique_ids):
            time.sleep(0.1)

    return results


def extract_track_id(uri: str) -> str | None:
    """Extract track ID from Spotify URI like 'spotify:track:3ibKnFDaa3GhpPGlOUj7ff'."""
    if not uri or not isinstance(uri, str):
        return None
    if uri.startswith("spotify:track:"):
        return uri.split(":")[-1]
    return None


def enrich_with_genres(
    artist_names: list[str],
    streaming_df=None,
    force_refresh: bool = False,
) -> dict[str, list[str]]:
    """
    Main function to get genres for artists.

    Uses cache when available, fetches from API when needed.
    Returns dict mapping artist_name -> list of genres.

    If API is not available, returns cached data only.
    """
    # Load existing cache
    cache = load_genre_cache()

    # If we have cached data and not forcing refresh, use it
    if cache and not force_refresh:
        # Map by artist name (cache stores by ID, but we can also store by name)
        return cache

    # Check if API is available
    if not is_api_available():
        print("Spotify API not configured. Using cached data only.")
        return cache

    token = get_access_token()
    if not token:
        print("Could not get Spotify access token. Using cached data only.")
        return cache

    # If we have streaming data, extract track IDs to find artist IDs
    if streaming_df is not None:
        # Get unique track URIs
        track_uris = streaming_df["spotify_track_uri"].dropna().unique()
        track_ids = [extract_track_id(uri) for uri in track_uris]
        track_ids = [tid for tid in track_ids if tid]

        # Fetch artist info for tracks
        print(f"Fetching artist info for {len(track_ids)} tracks...")
        track_artists = fetch_track_artists(track_ids[:1000], token)  # Limit for now

        # Collect unique artist IDs
        artist_ids = set()
        artist_id_to_name = {}
        for artists in track_artists.values():
            for artist in artists:
                artist_ids.add(artist["id"])
                artist_id_to_name[artist["id"]] = artist["name"]

        # Fetch genres for artists
        print(f"Fetching genres for {len(artist_ids)} artists...")
        artist_genres = fetch_artists_genres(list(artist_ids), token)

        # Build result mapping artist name -> genres
        result = {}
        for artist_id, genres in artist_genres.items():
            name = artist_id_to_name.get(artist_id)
            if name:
                result[name] = genres

        # Update and save cache
        cache.update(result)
        save_genre_cache(cache)
        print(f"Cached genres for {len(result)} artists.")

        return cache

    return cache


# Convenience function to check status
def print_status():
    """Print current API and cache status."""
    status = get_api_status()
    print("Spotify API Status:")
    print(f"  requests library: {'installed' if status['requests_installed'] else 'NOT INSTALLED'}")
    print(f"  SPOTIFY_CLIENT_ID: {'set' if status['client_id_set'] else 'NOT SET'}")
    print(f"  SPOTIFY_CLIENT_SECRET: {'set' if status['client_secret_set'] else 'NOT SET'}")
    print(f"  API available: {'YES' if status['credentials_configured'] else 'NO'}")
    print(f"  Genre cache: {status['cached_artists']} artists cached")


if __name__ == "__main__":
    print_status()
