"""
Spotify streaming history data loader and preprocessor.
Loads JSON files from StreamingHistory/ and prepares data for visualization.
"""

import json
from pathlib import Path
from functools import lru_cache

import pandas as pd


DATA_DIR = Path(__file__).parent / "StreamingHistory"

# Playlists to exclude from analysis
EXCLUDED_PLAYLISTS = [
    "SD/TB - Thanks 4 Sharing",
    "SD/TB - Client Confirmed Bangers",
]


def load_single_file(filepath: Path) -> list[dict]:
    """Load a single JSON streaming history file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_all_data() -> pd.DataFrame:
    """
    Load and combine all streaming history JSON files.
    Results are cached for performance.
    """
    all_records = []

    for filepath in sorted(DATA_DIR.glob("Streaming_History_Audio_*.json")):
        records = load_single_file(filepath)
        all_records.extend(records)

    df = pd.DataFrame(all_records)
    return preprocess_data(df)


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the raw streaming data.
    - Parse timestamps
    - Add time-based columns for analysis
    - Convert ms_played to minutes
    - Filter to music only (exclude podcasts/audiobooks)
    """
    # Parse timestamp
    df["ts"] = pd.to_datetime(df["ts"])

    # Add time-based columns for analysis
    df["year"] = df["ts"].dt.year
    df["month"] = df["ts"].dt.month
    df["day"] = df["ts"].dt.day
    df["hour"] = df["ts"].dt.hour
    df["day_of_week"] = df["ts"].dt.dayofweek  # 0=Monday, 6=Sunday
    df["day_name"] = df["ts"].dt.day_name()
    df["date"] = df["ts"].dt.date

    # Convert ms to minutes
    df["minutes_played"] = df["ms_played"] / 60000

    # Rename columns for clarity
    df = df.rename(columns={
        "master_metadata_track_name": "track",
        "master_metadata_album_artist_name": "artist",
        "master_metadata_album_album_name": "album",
    })

    # Filter to music only (has track name, no episode/audiobook)
    music_df = df[
        df["track"].notna() &
        df["episode_name"].isna() &
        df["audiobook_title"].isna()
    ].copy()

    return music_df


def get_track_stats(df: pd.DataFrame, track_name: str, artist_name: str = None) -> dict:
    """
    Get statistics for a specific track.
    Optionally filter by artist for tracks with same name.
    """
    mask = df["track"].str.lower() == track_name.lower()
    if artist_name:
        mask &= df["artist"].str.lower() == artist_name.lower()

    track_df = df[mask]

    if track_df.empty:
        return None

    return {
        "track": track_df["track"].iloc[0],
        "artist": track_df["artist"].iloc[0],
        "album": track_df["album"].iloc[0],
        "play_count": len(track_df),
        "total_minutes": track_df["minutes_played"].sum(),
        "first_played": track_df["ts"].min(),
        "last_played": track_df["ts"].max(),
        "plays_by_year": track_df.groupby("year").size().to_dict(),
        "plays_df": track_df,  # For detailed analysis
    }


def search_tracks(df: pd.DataFrame, query: str, limit: int = 50) -> pd.DataFrame:
    """
    Search for tracks matching a query string.
    Returns aggregated stats per unique track/artist combo.
    """
    query_lower = query.lower()

    # Search in track name, artist, and album
    mask = (
        df["track"].str.lower().str.contains(query_lower, na=False) |
        df["artist"].str.lower().str.contains(query_lower, na=False) |
        df["album"].str.lower().str.contains(query_lower, na=False)
    )

    matches = df[mask]

    if matches.empty:
        return pd.DataFrame()

    # Aggregate by track + artist
    stats = matches.groupby(["track", "artist", "album"]).agg(
        play_count=("ts", "count"),
        total_minutes=("minutes_played", "sum"),
        first_played=("ts", "min"),
        last_played=("ts", "max"),
    ).reset_index()

    stats = stats.sort_values("play_count", ascending=False).head(limit)
    return stats


def search_artists(df: pd.DataFrame, query: str, limit: int = 20) -> pd.DataFrame:
    """
    Search for artists matching a query string.
    Returns aggregated stats per artist.
    """
    query_lower = query.lower()
    mask = df["artist"].str.lower().str.contains(query_lower, na=False)
    matches = df[mask]

    if matches.empty:
        return pd.DataFrame()

    stats = matches.groupby("artist").agg(
        play_count=("ts", "count"),
        total_minutes=("minutes_played", "sum"),
        unique_tracks=("track", "nunique"),
        first_played=("ts", "min"),
        last_played=("ts", "max"),
    ).reset_index()

    stats = stats.sort_values("play_count", ascending=False).head(limit)
    return stats


def get_artist_plays(df: pd.DataFrame, artist_name: str) -> pd.DataFrame:
    """Get all plays for a specific artist."""
    mask = df["artist"].str.lower() == artist_name.lower()
    return df[mask].copy()


def get_top_albums(df: pd.DataFrame, year: int = None, limit: int = 20) -> pd.DataFrame:
    """Get top albums by play count, optionally filtered by year."""
    filtered = df if year is None else df[df["year"] == year]

    stats = filtered.groupby(["album", "artist"]).agg(
        play_count=("ts", "count"),
        total_minutes=("minutes_played", "sum"),
    ).reset_index()

    return stats.sort_values("play_count", ascending=False).head(limit)


def get_platform_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Get listening stats by platform."""
    # Simplify platform names
    df_copy = df.copy()

    def simplify_platform(p):
        if pd.isna(p):
            return "Unknown"
        p_lower = p.lower()
        if "iphone" in p_lower or "ios" in p_lower:
            return "iPhone"
        elif "android" in p_lower:
            return "Android"
        elif "windows" in p_lower:
            return "Windows"
        elif "mac" in p_lower or "osx" in p_lower:
            return "Mac"
        elif "web" in p_lower:
            return "Web Player"
        elif "linux" in p_lower:
            return "Linux"
        else:
            return "Other"

    df_copy["platform_simple"] = df_copy["platform"].apply(simplify_platform)

    stats = df_copy.groupby("platform_simple").agg(
        play_count=("ts", "count"),
        total_minutes=("minutes_played", "sum"),
    ).reset_index()

    return stats.sort_values("play_count", ascending=False)


def get_heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate heatmap data for day of week × hour of day.
    """
    heatmap = df.groupby(["day_of_week", "hour"]).size().reset_index(name="count")

    # Pivot for heatmap format
    pivot = heatmap.pivot(index="day_of_week", columns="hour", values="count").fillna(0)

    return pivot


def get_top_artists(df: pd.DataFrame, year: int = None, limit: int = 20, by: str = "plays") -> pd.DataFrame:
    """Get top artists by play count or minutes, optionally filtered by year."""
    filtered = df if year is None else df[df["year"] == year]

    stats = filtered.groupby("artist").agg(
        play_count=("ts", "count"),
        total_minutes=("minutes_played", "sum"),
    ).reset_index()

    sort_col = "play_count" if by == "plays" else "total_minutes"
    return stats.sort_values(sort_col, ascending=False).head(limit)


def get_top_tracks(df: pd.DataFrame, year: int = None, limit: int = 20, by: str = "plays") -> pd.DataFrame:
    """Get top tracks by play count or minutes, optionally filtered by year."""
    filtered = df if year is None else df[df["year"] == year]

    stats = filtered.groupby(["track", "artist"]).agg(
        play_count=("ts", "count"),
        total_minutes=("minutes_played", "sum"),
    ).reset_index()

    sort_col = "play_count" if by == "plays" else "total_minutes"
    return stats.sort_values(sort_col, ascending=False).head(limit)


def get_one_hit_wonders(df: pd.DataFrame, limit: int = 50) -> pd.DataFrame:
    """
    Get tracks that have only been played once ever.
    Filtered to: 2+ minutes played AND not on any playlist.
    """
    # Get tracks on playlists
    playlist_tracks = get_all_playlist_tracks()
    if not playlist_tracks.empty:
        playlist_set = set(zip(playlist_tracks["track"], playlist_tracks["artist"]))
    else:
        playlist_set = set()

    # Aggregate streaming data
    track_counts = df.groupby(["track", "artist", "album"]).agg(
        play_count=("ts", "count"),
        played_on=("ts", "first"),
        ms_played=("ms_played", "sum"),
    ).reset_index()

    # Filter: played exactly once, 2+ minutes, not on any playlist
    one_hits = track_counts[
        (track_counts["play_count"] == 1) &
        (track_counts["ms_played"] >= 120000)  # 2+ minutes
    ].copy()

    # Remove tracks that are on playlists
    one_hits["on_playlist"] = one_hits.apply(
        lambda row: (row["track"], row["artist"]) in playlist_set, axis=1
    )
    one_hits = one_hits[~one_hits["on_playlist"]]

    one_hits = one_hits.sort_values("played_on", ascending=False)
    return one_hits.head(limit)


def get_one_hit_wonder_stats(df: pd.DataFrame) -> dict:
    """Get overall stats about one-hit wonders (2+ min, not on playlist)."""
    # Get tracks on playlists
    playlist_tracks = get_all_playlist_tracks()
    if not playlist_tracks.empty:
        playlist_set = set(zip(playlist_tracks["track"], playlist_tracks["artist"]))
    else:
        playlist_set = set()

    track_counts = df.groupby(["track", "artist"]).agg(
        play_count=("ts", "count"),
        ms_played=("ms_played", "sum"),
    ).reset_index()

    # Filter to 2+ minutes
    track_counts = track_counts[track_counts["ms_played"] >= 120000]

    # Mark if on playlist
    track_counts["on_playlist"] = track_counts.apply(
        lambda row: (row["track"], row["artist"]) in playlist_set, axis=1
    )

    # One-hits: played once AND not on playlist
    one_hits = track_counts[
        (track_counts["play_count"] == 1) &
        (~track_counts["on_playlist"])
    ]

    total_unique_tracks = len(track_counts)
    one_hit_count = len(one_hits)

    return {
        "total_unique_tracks": total_unique_tracks,
        "one_hit_count": one_hit_count,
        "one_hit_percent": round(one_hit_count / total_unique_tracks * 100, 1) if total_unique_tracks > 0 else 0,
    }


def get_not_on_playlist_stats(df: pd.DataFrame) -> dict:
    """Get stats about tracks played but not on any playlist."""
    playlist_tracks = get_all_playlist_tracks()
    if not playlist_tracks.empty:
        playlist_set = set(zip(playlist_tracks["track"], playlist_tracks["artist"]))
    else:
        playlist_set = set()

    # Aggregate streaming data
    track_counts = df.groupby(["track", "artist"]).agg(
        play_count=("ts", "count"),
        total_minutes=("minutes_played", "sum"),
    ).reset_index()

    # Mark if on playlist
    track_counts["on_playlist"] = track_counts.apply(
        lambda row: (row["track"], row["artist"]) in playlist_set, axis=1
    )

    on_playlist = track_counts[track_counts["on_playlist"]]
    not_on_playlist = track_counts[~track_counts["on_playlist"]]

    return {
        "total_unique_tracks": len(track_counts),
        "on_playlist_count": len(on_playlist),
        "not_on_playlist_count": len(not_on_playlist),
        "not_on_playlist_percent": round(len(not_on_playlist) / len(track_counts) * 100, 1) if len(track_counts) > 0 else 0,
        "not_on_playlist_plays": not_on_playlist["play_count"].sum(),
        "not_on_playlist_minutes": not_on_playlist["total_minutes"].sum(),
    }


def get_top_not_on_playlist(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Get most played tracks that are NOT on any playlist."""
    playlist_tracks = get_all_playlist_tracks()
    if not playlist_tracks.empty:
        playlist_set = set(zip(playlist_tracks["track"], playlist_tracks["artist"]))
    else:
        playlist_set = set()

    # Aggregate streaming data
    track_counts = df.groupby(["track", "artist", "album"]).agg(
        play_count=("ts", "count"),
        total_minutes=("minutes_played", "sum"),
        last_played=("ts", "max"),
    ).reset_index()

    # Filter to NOT on playlist
    track_counts["on_playlist"] = track_counts.apply(
        lambda row: (row["track"], row["artist"]) in playlist_set, axis=1
    )
    not_on_playlist = track_counts[~track_counts["on_playlist"]].copy()

    return not_on_playlist.sort_values("play_count", ascending=False).head(limit)


def get_most_skipped(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Get most skipped tracks."""
    skipped = df[df["skipped"] == True]

    stats = skipped.groupby(["track", "artist"]).agg(
        skip_count=("ts", "count"),
    ).reset_index()

    return stats.sort_values("skip_count", ascending=False).head(limit)


def get_listening_over_time(df: pd.DataFrame, period: str = "M") -> pd.DataFrame:
    """
    Get listening activity over time.
    period: 'D' for daily, 'W' for weekly, 'M' for monthly, 'Y' for yearly
    """
    df_copy = df.copy()
    df_copy["period"] = df_copy["ts"].dt.to_period(period)

    stats = df_copy.groupby("period").agg(
        play_count=("ts", "count"),
        total_minutes=("minutes_played", "sum"),
        unique_tracks=("track", "nunique"),
        unique_artists=("artist", "nunique"),
    ).reset_index()

    stats["period"] = stats["period"].astype(str)
    return stats


# ============ Playlist Data Loaders ============

@lru_cache(maxsize=1)
def load_playlists() -> dict:
    """Load playlist data from Playlist1.json."""
    filepath = DATA_DIR / "Playlist1.json"
    if not filepath.exists():
        return {"playlists": []}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_playlist_names() -> list[str]:
    """Get list of all playlist names (excluding filtered playlists)."""
    data = load_playlists()
    return [
        p.get("name", "Unknown")
        for p in data.get("playlists", [])
        if p.get("name") not in EXCLUDED_PLAYLISTS
    ]


def get_playlist_stats() -> pd.DataFrame:
    """Get stats for each playlist (excluding filtered playlists)."""
    data = load_playlists()
    playlists = data.get("playlists", [])

    stats = []
    for p in playlists:
        if p.get("name") in EXCLUDED_PLAYLISTS:
            continue
        items = p.get("items", [])
        track_items = [i for i in items if i.get("track")]
        artists = set(i["track"].get("artistName") for i in track_items if i.get("track"))
        stats.append({
            "name": p.get("name", "Unknown"),
            "track_count": len(track_items),
            "unique_artists": len(artists),
            "last_modified": p.get("lastModifiedDate"),
            "collaborators": len(p.get("collaborators", [])),
        })

    df = pd.DataFrame(stats)
    if not df.empty:
        df = df.sort_values("track_count", ascending=False)
    return df


@lru_cache(maxsize=1)
def get_all_playlist_tracks() -> pd.DataFrame:
    """Get all tracks from all playlists (excluding filtered playlists)."""
    data = load_playlists()
    playlists = data.get("playlists", [])

    tracks = []
    for p in playlists:
        playlist_name = p.get("name", "Unknown")
        if playlist_name in EXCLUDED_PLAYLISTS:
            continue
        for item in p.get("items", []):
            if item.get("track"):
                track = item["track"]
                tracks.append({
                    "playlist": playlist_name,
                    "track": track.get("trackName"),
                    "artist": track.get("artistName"),
                    "album": track.get("albumName"),
                    "uri": track.get("trackUri"),
                })

    return pd.DataFrame(tracks)


def get_playlist_top_artists(playlist_name: str, limit: int = 15) -> pd.DataFrame:
    """Get top artists in a specific playlist."""
    df = get_all_playlist_tracks()
    if df.empty:
        return pd.DataFrame()

    playlist_df = df[df["playlist"] == playlist_name]
    if playlist_df.empty:
        return pd.DataFrame()

    stats = playlist_df.groupby("artist").size().reset_index(name="track_count")
    return stats.sort_values("track_count", ascending=False).head(limit)


def get_playlist_tracks(playlist_name: str) -> pd.DataFrame:
    """Get all tracks for a specific playlist."""
    df = get_all_playlist_tracks()
    if df.empty:
        return pd.DataFrame()

    return df[df["playlist"] == playlist_name].copy()


def get_artist_playlist_distribution(limit: int = 20) -> pd.DataFrame:
    """Get artists that appear in the most playlists."""
    df = get_all_playlist_tracks()
    if df.empty:
        return pd.DataFrame()

    # Count unique playlists per artist
    artist_playlists = df.groupby("artist").agg(
        playlist_count=("playlist", "nunique"),
        track_count=("track", "count"),
        playlists=("playlist", lambda x: list(x.unique())),
    ).reset_index()

    return artist_playlists.sort_values("playlist_count", ascending=False).head(limit)


def get_track_duplicates() -> pd.DataFrame:
    """Get tracks that appear in multiple playlists."""
    df = get_all_playlist_tracks()
    if df.empty:
        return pd.DataFrame()

    # Group by track + artist and count playlists
    dupes = df.groupby(["track", "artist"]).agg(
        playlist_count=("playlist", "nunique"),
        playlists=("playlist", lambda x: list(x.unique())),
    ).reset_index()

    # Only keep tracks in 2+ playlists
    dupes = dupes[dupes["playlist_count"] > 1]
    return dupes.sort_values("playlist_count", ascending=False)


def get_playlist_overlap(playlist1: str, playlist2: str) -> dict:
    """Compare two playlists and find overlapping artists/tracks."""
    df = get_all_playlist_tracks()
    if df.empty:
        return {}

    p1 = df[df["playlist"] == playlist1]
    p2 = df[df["playlist"] == playlist2]

    p1_artists = set(p1["artist"].unique())
    p2_artists = set(p2["artist"].unique())
    shared_artists = p1_artists & p2_artists

    p1_tracks = set(zip(p1["track"], p1["artist"]))
    p2_tracks = set(zip(p2["track"], p2["artist"]))
    shared_tracks = p1_tracks & p2_tracks

    return {
        "playlist1": playlist1,
        "playlist2": playlist2,
        "p1_track_count": len(p1),
        "p2_track_count": len(p2),
        "p1_artist_count": len(p1_artists),
        "p2_artist_count": len(p2_artists),
        "shared_artists": list(shared_artists),
        "shared_artist_count": len(shared_artists),
        "shared_tracks": [{"track": t, "artist": a} for t, a in shared_tracks],
        "shared_track_count": len(shared_tracks),
    }


def get_playlist_track_overlaps(playlist_name: str) -> pd.DataFrame:
    """Find tracks in this playlist that also appear in other playlists."""
    df = get_all_playlist_tracks()
    if df.empty:
        return pd.DataFrame()

    # Get tracks in the selected playlist
    playlist_tracks = df[df["playlist"] == playlist_name][["track", "artist"]].drop_duplicates()

    if playlist_tracks.empty:
        return pd.DataFrame()

    # Find which of these tracks appear in OTHER playlists
    results = []
    for _, row in playlist_tracks.iterrows():
        track, artist = row["track"], row["artist"]
        # Find all playlists containing this track (excluding the current one)
        other_playlists = df[
            (df["track"] == track) &
            (df["artist"] == artist) &
            (df["playlist"] != playlist_name)
        ]["playlist"].unique().tolist()

        if other_playlists:
            results.append({
                "track": track,
                "artist": artist,
                "other_playlists": other_playlists,
                "overlap_count": len(other_playlists),
            })

    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values("overlap_count", ascending=False)
    return result_df


def get_overall_playlist_summary() -> dict:
    """Get overall summary stats for all playlists."""
    df = get_all_playlist_tracks()
    stats = get_playlist_stats()

    if df.empty:
        return {}

    return {
        "total_playlists": len(stats),
        "total_tracks": len(df),
        "unique_tracks": df.drop_duplicates(subset=["track", "artist"]).shape[0],
        "unique_artists": df["artist"].nunique(),
        "avg_playlist_size": round(stats["track_count"].mean(), 1) if not stats.empty else 0,
        "largest_playlist": stats.iloc[0]["name"] if not stats.empty else "",
        "largest_playlist_size": stats.iloc[0]["track_count"] if not stats.empty else 0,
    }
