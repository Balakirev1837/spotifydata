# Spotify API Integration Reference

## Overview

This document outlines how to integrate the Spotify Web API to fetch genre data for artists in our streaming history.

## Setup Requirements

### 1. Create a Spotify Developer App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Note your credentials:
   - **Client ID**: Public identifier
   - **Client Secret**: Keep confidential

### 2. Environment Variables

Store credentials securely (never commit to git):

```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

## Authentication

### Client Credentials Flow

Best for our use case (fetching public artist data, no user-specific data needed).

**Request Access Token:**
```
POST https://accounts.spotify.com/api/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}
```

**Response:**
```json
{
  "access_token": "BQDj...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

- Tokens expire after **3600 seconds (1 hour)**
- Include in all API requests: `Authorization: Bearer {access_token}`

## Relevant Endpoints

### Get Multiple Artists (Batch)

Fetch up to **50 artists per request** - use this for efficiency.

```
GET https://api.spotify.com/v1/artists?ids={comma_separated_ids}
```

**Example:**
```
GET https://api.spotify.com/v1/artists?ids=0TnOYISbd1XYRBk9myaseg,3TVXtAsR1Inumwj472S9r4
```

**Response includes:**
- `genres`: Array of genre strings (e.g., `["prog rock", "grunge"]`)
- `name`: Artist name
- `popularity`: 0-100 score
- `followers.total`: Follower count

### Get Single Artist

```
GET https://api.spotify.com/v1/artists/{id}
```

## Rate Limits

- Based on rolling **30-second window**
- Returns **HTTP 429** when exceeded
- Check `Retry-After` header for wait time

### Best Practices

1. **Batch requests**: Always use the multi-artist endpoint (50 at a time)
2. **Cache results**: Store artist genres locally to avoid re-fetching
3. **Implement backoff**: Wait and retry on 429 errors
4. **Lazy loading**: Don't fetch all at once on startup

## Data Mapping

Our streaming history contains `spotify_track_uri` like:
```
spotify:track:3ibKnFDaa3GhpPGlOUj7ff
```

We need artist IDs. Options:
1. Extract from streaming history (if available)
2. Use Search API to find artist by name
3. Use Get Track endpoint to get artist ID from track

### Get Track (to find Artist ID)

```
GET https://api.spotify.com/v1/tracks/{track_id}
```

Returns `artists` array with artist IDs.

## Implementation Plan

### Phase 1: Basic Integration
1. Create `spotify_api.py` module
2. Implement authentication (client credentials)
3. Implement `get_artists_genres(artist_ids)` function

### Phase 2: Data Enrichment
1. Build artist ID mapping from track URIs
2. Batch fetch artist genres (50 at a time)
3. Cache results to JSON/SQLite to avoid re-fetching

### Phase 3: Visualization
1. Add genre breakdown charts to dashboard
2. Show top genres by plays/minutes
3. Genre trends over time

## Dependencies

```
pip install requests
```
Or with uv:
```
uv add requests
```

## Example Code Structure

```python
# spotify_api.py

import os
import requests
from functools import lru_cache

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

def get_access_token() -> str:
    """Get access token using client credentials flow."""
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["SPOTIFY_CLIENT_ID"],
            "client_secret": os.environ["SPOTIFY_CLIENT_SECRET"],
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_artists_genres(artist_ids: list[str], token: str) -> dict[str, list[str]]:
    """Fetch genres for multiple artists (max 50 per call)."""
    results = {}

    # Batch in chunks of 50
    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i+50]
        response = requests.get(
            f"{SPOTIFY_API_BASE}/artists",
            params={"ids": ",".join(batch)},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()

        for artist in response.json()["artists"]:
            if artist:
                results[artist["id"]] = artist.get("genres", [])

    return results
```

## Notes

- Genres are associated with **artists**, not tracks
- Some artists have no genres (empty array) if not yet classified by Spotify
- Genre names are lowercase strings like "pop", "indie rock", "k-pop"
