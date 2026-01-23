# Spotify Streaming History Dashboard

A Streamlit-based web dashboard for visualizing your Spotify listening history data.

## Project Structure

```
spotifydata/
├── app.py              # Main Streamlit dashboard application
├── data_loader.py      # Data loading and processing utilities
├── spotify_api.py      # Spotify API integration for genre data
├── main.py             # Entry point (placeholder)
├── pyproject.toml      # Project configuration and dependencies
├── uv.lock             # Dependency lock file
├── AGENTS.md           # Agent documentation
├── SPOTIFY_API.md      # Spotify API setup guide
├── StreamingHistory/   # Your Spotify data export files
│   ├── Streaming_History_Audio_*.json  # Extended streaming history
│   ├── StreamingHistory_music_*.json   # Standard streaming history
│   ├── Playlist1.json                  # Playlist data
│   ├── YourLibrary.json                # Library data
│   └── ...                             # Other Spotify export files
└── .venv/              # Python virtual environment
```

## Server Tasks

### Start the Server

```bash
uv run streamlit run app.py --server.headless true
```

The server will be available at:
- **Local:** http://localhost:8501
- **Network:** http://[your-ip]:8501

### Start with Custom Port

```bash
uv run streamlit run app.py --server.port 8080 --server.headless true
```

### Start for Digital Signage (Kiosk Mode)

```bash
uv run streamlit run app.py --server.headless true --server.runOnSave false
```

### Stop the Server

Press `Ctrl+C` in the terminal where the server is running.

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Add Your Spotify Data

1. Request your data from Spotify: Account → Privacy Settings → Download your data
2. Place the exported JSON files in the `StreamingHistory/` directory

### 3. (Optional) Enable Genre Analysis

To enable genre analysis, set up Spotify API credentials:

1. Create an app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Set environment variables:
   ```bash
   export SPOTIFY_CLIENT_ID=your_client_id
   export SPOTIFY_CLIENT_SECRET=your_client_secret
   ```

See `SPOTIFY_API.md` for detailed setup instructions.

## Features

- **Dashboard:** Top albums, artists, tracks by plays and listening time
- **Search:** Look up specific tracks or artists with detailed stats
- **Playlists:** Analyze playlist contents, overlaps, and track distribution
- **Genres:** View genre trends over time (requires Spotify API setup)
- **Activity Heatmaps:** See when you listen to music throughout the week
