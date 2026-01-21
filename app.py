"""
Spotify Streaming History Dashboard

A Streamlit app for visualizing Spotify listening data.
Designed to be deployable as a webserver for digital signage.

Run with: uv run streamlit run app.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from data_loader import (
    load_all_data,
    search_tracks,
    search_artists,
    get_artist_plays,
    get_track_stats,
    get_heatmap_data,
    get_top_artists,
    get_top_tracks,
    get_top_albums,
    get_most_skipped,
    get_one_hit_wonders,
    get_one_hit_wonder_stats,
    get_not_on_playlist_stats,
    get_top_not_on_playlist,
    get_playlist_names,
    get_playlist_stats,
    get_playlist_top_artists,
    get_playlist_tracks,
    get_playlist_track_overlaps,
    get_artist_playlist_distribution,
    get_track_duplicates,
    get_playlist_overlap,
    get_overall_playlist_summary,
    get_genre_status,
    get_top_genres,
    get_genre_trends,
    get_artist_genre,
)


# Page config - wide layout works well for digital signs
st.set_page_config(
    page_title="Spotify Stats",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for cleaner display (useful for digital signage)
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1 {
        font-size: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def get_data():
    """Load data with Streamlit caching."""
    return load_all_data()


def render_heatmap(df: pd.DataFrame, title: str = "Listening Activity", colorscale: str = "Greens"):
    """Render a listening activity heatmap."""
    heatmap_data = get_heatmap_data(df)

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=list(range(24)),
        y=day_names,
        colorscale=colorscale,
        hovertemplate="Day: %{y}<br>Hour: %{x}:00<br>Plays: %{z}<extra></extra>",
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        xaxis=dict(tickmode="linear", dtick=2),
        height=350,
        margin=dict(l=0, r=0, t=40, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_top_albums(df: pd.DataFrame, year: int = None):
    """Render top albums bar chart."""
    top = get_top_albums(df, year=year, limit=20)
    top["label"] = top["album"] + " - " + top["artist"]

    fig = px.bar(
        top,
        x="play_count",
        y="label",
        orientation="h",
        title=f"Top Albums {f'({year})' if year else '(All Time)'}",
        labels={"play_count": "Play Count", "label": ""},
        color="total_minutes",
        color_continuous_scale="Purples",
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_top_artists(df: pd.DataFrame, year: int = None):
    """Render top artists bar chart."""
    top = get_top_artists(df, year=year, limit=20)

    fig = px.bar(
        top,
        x="play_count",
        y="artist",
        orientation="h",
        title=f"Top Artists {f'({year})' if year else '(All Time)'}",
        labels={"play_count": "Play Count", "artist": ""},
        color="total_minutes",
        color_continuous_scale="Greens",
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_top_tracks(df: pd.DataFrame, year: int = None):
    """Render top tracks by play count bar chart."""
    top = get_top_tracks(df, year=year, limit=20, by="plays")
    top["label"] = top["track"] + " - " + top["artist"]

    fig = px.bar(
        top,
        x="play_count",
        y="label",
        orientation="h",
        title=f"Top Tracks by Plays {f'({year})' if year else '(All Time)'}",
        labels={"play_count": "Play Count", "label": ""},
        color="total_minutes",
        color_continuous_scale="Blues",
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_top_tracks_by_minutes(df: pd.DataFrame, year: int = None):
    """Render top tracks by total minutes bar chart."""
    top = get_top_tracks(df, year=year, limit=20, by="minutes")
    top["label"] = top["track"] + " - " + top["artist"]

    fig = px.bar(
        top,
        x="total_minutes",
        y="label",
        orientation="h",
        title=f"Top Tracks by Minutes {f'({year})' if year else '(All Time)'}",
        labels={"total_minutes": "Minutes Listened", "label": ""},
        color="play_count",
        color_continuous_scale="Oranges",
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_one_hit_wonders(df: pd.DataFrame):
    """Render one-hit wonders stats and list."""
    stats = get_one_hit_wonder_stats(df)
    wonders = get_one_hit_wonders(df, limit=20)

    st.markdown(f"### One-Hit Wonders")
    st.caption(f"{stats['one_hit_count']:,} tracks ({stats['one_hit_percent']}%) played once, 2+ min, not on any playlist")

    if not wonders.empty:
        wonders_display = wonders[["track", "artist", "played_on"]].copy()
        wonders_display["played_on"] = pd.to_datetime(wonders_display["played_on"]).dt.strftime("%Y-%m-%d")
        wonders_display = wonders_display.rename(columns={
            "track": "Track",
            "artist": "Artist",
            "played_on": "Played On",
        })
        st.dataframe(wonders_display, use_container_width=True, hide_index=True, height=480)
    else:
        st.info("No one-hit wonders found")


def render_not_on_playlist(df: pd.DataFrame):
    """Render stats and top tracks not on any playlist."""
    stats = get_not_on_playlist_stats(df)
    top = get_top_not_on_playlist(df, limit=20)

    st.markdown("### Not On Any Playlist")
    st.caption(f"{stats['not_on_playlist_count']:,} tracks ({stats['not_on_playlist_percent']}%) played but not saved to playlists")

    if not top.empty:
        top_display = top.copy()
        top_display["label"] = top_display["track"] + " - " + top_display["artist"]

        fig = px.bar(
            top_display,
            x="play_count",
            y="label",
            orientation="h",
            title="Most Played (Not on Playlist)",
            labels={"play_count": "Plays", "label": ""},
            color="total_minutes",
            color_continuous_scale="Reds",
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=550,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False,
            coloraxis_showscale=False,
        )

        st.plotly_chart(fig, use_container_width=True)


def render_most_skipped(df: pd.DataFrame):
    """Render most skipped tracks bar chart."""
    top = get_most_skipped(df, limit=20)
    top["label"] = top["track"] + " - " + top["artist"]

    fig = px.bar(
        top,
        x="skip_count",
        y="label",
        orientation="h",
        title="Most Skipped Tracks",
        labels={"skip_count": "Skip Count", "label": ""},
        color="skip_count",
        color_continuous_scale="Reds",
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        height=550,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_search_results(df: pd.DataFrame, query: str):
    """Render search results for a track/artist query."""
    results = search_tracks(df, query)

    if results.empty:
        st.warning(f"No results found for '{query}'")
        return

    st.subheader(f"Search Results for '{query}'")

    # Show results table
    display_df = results.copy()
    display_df["total_minutes"] = display_df["total_minutes"].round(1)
    display_df = display_df.rename(columns={
        "track": "Track",
        "artist": "Artist",
        "album": "Album",
        "play_count": "Plays",
        "total_minutes": "Minutes",
        "first_played": "First Played",
        "last_played": "Last Played",
    })

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    # If there's a top result, show detailed stats
    if len(results) > 0:
        top_result = results.iloc[0]
        stats = get_track_stats(df, top_result["track"], top_result["artist"])

        if stats:
            st.markdown("---")
            st.subheader(f"Details: {stats['track']}")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Plays", stats["play_count"])
            col2.metric("Total Minutes", f"{stats['total_minutes']:.1f}")
            col3.metric("First Played", stats["first_played"].strftime("%Y-%m-%d"))
            col4.metric("Last Played", stats["last_played"].strftime("%Y-%m-%d"))

            # Plays by year chart
            if stats["plays_by_year"]:
                year_df = pd.DataFrame(
                    list(stats["plays_by_year"].items()),
                    columns=["Year", "Plays"]
                )

                fig = px.bar(
                    year_df,
                    x="Year",
                    y="Plays",
                    title="Plays by Year",
                )
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)

            # Show play history heatmap for this track
            render_track_heatmap(stats["plays_df"])


def render_track_heatmap(plays_df: pd.DataFrame):
    """Render a heatmap for a specific track's play history."""
    heatmap_data = get_heatmap_data(plays_df)

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=list(range(24)),
        y=day_names,
        colorscale="Blues",
        hovertemplate="Day: %{y}<br>Hour: %{x}:00<br>Plays: %{z}<extra></extra>",
    ))

    fig.update_layout(
        title="When You Listen to This Track",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        xaxis=dict(tickmode="linear", dtick=2),
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_artist_search_results(df: pd.DataFrame, query: str):
    """Render search results for an artist query with heatmap."""
    results = search_artists(df, query)

    if results.empty:
        st.warning(f"No artists found for '{query}'")
        return

    st.subheader(f"Artist Results for '{query}'")

    # Show results table
    display_df = results.copy()
    display_df["total_minutes"] = display_df["total_minutes"].round(1)
    display_df = display_df.rename(columns={
        "artist": "Artist",
        "play_count": "Plays",
        "total_minutes": "Minutes",
        "unique_tracks": "Unique Tracks",
        "first_played": "First Played",
        "last_played": "Last Played",
    })

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    # Show details for the top result
    if len(results) > 0:
        top_artist = results.iloc[0]["artist"]
        artist_plays = get_artist_plays(df, top_artist)

        st.markdown("---")
        st.subheader(f"Details: {top_artist}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Plays", f"{len(artist_plays):,}")
        col2.metric("Unique Tracks", f"{artist_plays['track'].nunique():,}")
        col3.metric("Hours Listened", f"{artist_plays['minutes_played'].sum() / 60:.1f}")
        col4.metric("First Played", artist_plays["ts"].min().strftime("%Y-%m-%d"))

        # Heatmap for this artist
        render_heatmap(artist_plays, title=f"When You Listen to {top_artist}", colorscale="Purples")

        # Top tracks by this artist
        st.subheader(f"Top Tracks by {top_artist}")
        top_tracks = artist_plays.groupby("track").agg(
            play_count=("ts", "count"),
            total_minutes=("minutes_played", "sum"),
        ).reset_index().sort_values("play_count", ascending=False).head(10)

        fig = px.bar(
            top_tracks,
            x="play_count",
            y="track",
            orientation="h",
            labels={"play_count": "Plays", "track": ""},
            color="total_minutes",
            color_continuous_scale="Purples",
        )
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, use_container_width=True)


def render_stats_overview(df: pd.DataFrame):
    """Render overview statistics."""
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Plays", f"{len(df):,}")
    col2.metric("Unique Tracks", f"{df['track'].nunique():,}")
    col3.metric("Unique Artists", f"{df['artist'].nunique():,}")
    col4.metric("Hours Listened", f"{df['minutes_played'].sum() / 60:,.0f}")


def main():
    st.title("Spotify Listening History")

    # Load data
    with st.spinner("Loading data..."):
        df = get_data()

    # Overview stats
    render_stats_overview(df)

    st.markdown("---")

    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Search", "Playlists", "Genres"])

    with tab1:
        # Year filter
        years = sorted(df["year"].unique())
        selected_year = st.selectbox(
            "Filter by Year",
            options=[None] + years,
            format_func=lambda x: "All Time" if x is None else str(x),
            key="dashboard_year",
        )

        filtered_df = df if selected_year is None else df[df["year"] == selected_year]

        # Top albums and top artists
        col1, col2 = st.columns(2)
        with col1:
            render_top_albums(df, year=selected_year)
        with col2:
            render_top_artists(df, year=selected_year)

        st.markdown("---")

        # Top tracks by plays and by minutes
        col1, col2 = st.columns(2)
        with col1:
            render_top_tracks(df, year=selected_year)
        with col2:
            render_top_tracks_by_minutes(df, year=selected_year)

        st.markdown("---")

        # Most skipped and one-hit wonders
        col1, col2 = st.columns(2)
        with col1:
            render_most_skipped(filtered_df)
        with col2:
            render_one_hit_wonders(df)

        st.markdown("---")

        # Not on any playlist
        render_not_on_playlist(df)

    with tab2:
        st.subheader("Search")

        search_type = st.radio(
            "Search for:",
            ["Tracks", "Artists"],
            horizontal=True,
        )

        query = st.text_input(
            f"Search for {'a track or album' if search_type == 'Tracks' else 'an artist'}",
            placeholder="e.g., Bohemian Rhapsody, Abbey Road..." if search_type == "Tracks" else "e.g., The Beatles, Taylor Swift...",
        )

        if query:
            if search_type == "Tracks":
                render_search_results(df, query)
            else:
                render_artist_search_results(df, query)

    with tab3:
        st.subheader("Playlist Analysis")

        # Overall summary
        summary = get_overall_playlist_summary()
        playlist_stats = get_playlist_stats()

        if summary:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Playlists", summary["total_playlists"])
            col2.metric("Total Tracks", f"{summary['total_tracks']:,}")
            col3.metric("Unique Tracks", f"{summary['unique_tracks']:,}")
            col4.metric("Unique Artists", f"{summary['unique_artists']:,}")

        st.markdown("---")

        # Playlist sizes chart
        if not playlist_stats.empty:
            st.markdown("### Playlist Sizes")
            top_playlists = playlist_stats.head(20)
            fig = px.bar(
                top_playlists,
                x="track_count",
                y="name",
                orientation="h",
                title="Tracks per Playlist",
                labels={"track_count": "Tracks", "name": ""},
                color="unique_artists",
                color_continuous_scale="Viridis",
                hover_data=["unique_artists"],
            )
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                height=550,
                margin=dict(l=0, r=0, t=40, b=0),
                coloraxis_colorbar_title="Artists",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Playlist deep dive
        st.markdown("### Explore a Playlist")
        playlist_names = get_playlist_names()

        if playlist_names:
            selected_playlist = st.selectbox(
                "Select a playlist",
                options=playlist_names,
                key="playlist_select",
            )

            if selected_playlist:
                col1, col2 = st.columns(2)

                with col1:
                    # Top artists in this playlist
                    top_artists = get_playlist_top_artists(selected_playlist, limit=15)
                    if not top_artists.empty:
                        fig = px.bar(
                            top_artists,
                            x="track_count",
                            y="artist",
                            orientation="h",
                            title=f"Top Artists in '{selected_playlist}'",
                            labels={"track_count": "Tracks", "artist": ""},
                            color="track_count",
                            color_continuous_scale="Blues",
                        )
                        fig.update_layout(
                            yaxis=dict(autorange="reversed"),
                            height=450,
                            margin=dict(l=0, r=0, t=40, b=0),
                            showlegend=False,
                            coloraxis_showscale=False,
                        )
                        st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Track list for this playlist
                    tracks = get_playlist_tracks(selected_playlist)
                    if not tracks.empty:
                        st.markdown(f"**{len(tracks)} tracks**")
                        display_df = tracks[["track", "artist", "album"]].rename(columns={
                            "track": "Track",
                            "artist": "Artist",
                            "album": "Album",
                        })
                        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

                # Tracks that appear in other playlists
                overlaps = get_playlist_track_overlaps(selected_playlist)
                if not overlaps.empty:
                    st.markdown(f"#### Tracks Also in Other Playlists ({len(overlaps)} found)")
                    st.caption("These tracks from this playlist also appear elsewhere - consider removing for freshness")

                    overlap_display = overlaps.copy()
                    overlap_display["other_playlists_str"] = overlap_display["other_playlists"].apply(lambda x: ", ".join(x))
                    overlap_display = overlap_display[["track", "artist", "overlap_count", "other_playlists_str"]].rename(columns={
                        "track": "Track",
                        "artist": "Artist",
                        "overlap_count": "# Other Playlists",
                        "other_playlists_str": "Also In",
                    })
                    st.dataframe(overlap_display, use_container_width=True, hide_index=True)
                else:
                    st.success("No overlapping tracks - this playlist is unique!")

        st.markdown("---")

        # Compare playlists
        st.markdown("### Compare Playlists")
        if len(playlist_names) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                playlist1 = st.selectbox("First playlist", playlist_names, key="compare1")
            with col2:
                playlist2 = st.selectbox("Second playlist", playlist_names, index=1, key="compare2")

            if playlist1 and playlist2 and playlist1 != playlist2:
                overlap = get_playlist_overlap(playlist1, playlist2)

                col1, col2, col3 = st.columns(3)
                col1.metric(f"{playlist1}", f"{overlap['p1_track_count']} tracks")
                col2.metric("Shared Artists", overlap['shared_artist_count'])
                col3.metric(f"{playlist2}", f"{overlap['p2_track_count']} tracks")

                if overlap['shared_tracks']:
                    st.markdown(f"**{overlap['shared_track_count']} shared tracks:**")
                    shared_df = pd.DataFrame(overlap['shared_tracks'])
                    shared_df = shared_df.rename(columns={"track": "Track", "artist": "Artist"})
                    st.dataframe(shared_df, use_container_width=True, hide_index=True)

                if overlap['shared_artists']:
                    with st.expander(f"View {overlap['shared_artist_count']} shared artists"):
                        st.write(", ".join(sorted(overlap['shared_artists'])))

        st.markdown("---")

        # Cross-playlist analysis
        st.markdown("### Cross-Playlist Insights")

        col1, col2 = st.columns(2)

        with col1:
            # Artists in the most playlists
            st.markdown("**Artists in Most Playlists**")
            artist_dist = get_artist_playlist_distribution(limit=15)
            if not artist_dist.empty:
                fig = px.bar(
                    artist_dist,
                    x="playlist_count",
                    y="artist",
                    orientation="h",
                    labels={"playlist_count": "Playlists", "artist": ""},
                    color="track_count",
                    color_continuous_scale="Greens",
                    hover_data=["track_count"],
                )
                fig.update_layout(
                    yaxis=dict(autorange="reversed"),
                    height=450,
                    margin=dict(l=0, r=0, t=10, b=0),
                    showlegend=False,
                    coloraxis_colorbar_title="Tracks",
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Duplicate tracks across playlists
            st.markdown("**Tracks in Multiple Playlists**")
            dupes = get_track_duplicates()
            if not dupes.empty:
                dupes_display = dupes.head(15).copy()
                dupes_display["label"] = dupes_display["track"] + " - " + dupes_display["artist"]
                fig = px.bar(
                    dupes_display,
                    x="playlist_count",
                    y="label",
                    orientation="h",
                    labels={"playlist_count": "Playlists", "label": ""},
                    color="playlist_count",
                    color_continuous_scale="Oranges",
                )
                fig.update_layout(
                    yaxis=dict(autorange="reversed"),
                    height=450,
                    margin=dict(l=0, r=0, t=10, b=0),
                    showlegend=False,
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No tracks appear in multiple playlists")

    with tab4:
        st.subheader("Genre Analysis")

        # Check genre data status
        genre_status = get_genre_status()

        if not genre_status["has_genre_data"]:
            st.warning("Genre data not available yet.")
            st.markdown("""
            ### Setup Required

            To enable genre analysis, you need to:

            1. **Create a Spotify Developer App** at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
            2. **Set environment variables:**
               ```
               SPOTIFY_CLIENT_ID=your_client_id
               SPOTIFY_CLIENT_SECRET=your_client_secret
               ```
            3. **Restart the app** to fetch genre data

            Once configured, the app will automatically fetch and cache genre data for your artists.
            """)

            col1, col2 = st.columns(2)
            col1.metric("API Configured", "Yes" if genre_status["api_available"] else "No")
            col2.metric("Cached Artists", genre_status["cached_artists"])

        else:
            # Genre data available - show visualizations
            col1, col2 = st.columns(4)
            col1.metric("Cached Artists", genre_status["cached_artists"])

            st.markdown("---")

            # Top genres
            st.markdown("### Top Genres")
            top_genres = get_top_genres(df, limit=20)

            if not top_genres.empty:
                col1, col2 = st.columns(2)

                with col1:
                    fig = px.bar(
                        top_genres,
                        x="play_count",
                        y="genre",
                        orientation="h",
                        title="Genres by Play Count",
                        labels={"play_count": "Plays", "genre": ""},
                        color="total_minutes",
                        color_continuous_scale="Viridis",
                    )
                    fig.update_layout(
                        yaxis=dict(autorange="reversed"),
                        height=550,
                        margin=dict(l=0, r=0, t=40, b=0),
                        showlegend=False,
                        coloraxis_showscale=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Pie chart of top genres
                    top_10 = top_genres.head(10)
                    fig = px.pie(
                        top_10,
                        values="play_count",
                        names="genre",
                        title="Top 10 Genres Distribution",
                        hole=0.4,
                    )
                    fig.update_layout(
                        height=550,
                        margin=dict(l=0, r=0, t=40, b=0),
                    )
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            # Genre trends over time
            st.markdown("### Genre Trends Over Time")
            trends = get_genre_trends(df, top_n=5)

            if not trends.empty:
                fig = px.line(
                    trends,
                    x="period",
                    y="play_count",
                    color="genre",
                    title="Top 5 Genres Over Time",
                    labels={"period": "Month", "play_count": "Plays", "genre": "Genre"},
                )
                fig.update_layout(
                    height=400,
                    margin=dict(l=0, r=0, t=40, b=0),
                    xaxis=dict(tickangle=45),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for genre trends")


if __name__ == "__main__":
    main()
