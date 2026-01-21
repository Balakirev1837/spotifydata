# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Project Overview

**Spotify Streaming History Visualizer** - A Python/Streamlit dashboard for visualizing Spotify listening data. Designed to be deployable as a webserver for digital signage.

### Tech Stack
- **Python 3.13+** with **uv** for package management
- **pandas** - Data processing
- **plotly** - Interactive visualizations
- **Streamlit** - Web dashboard framework

### Project Structure
```
spotifydata/
├── StreamingHistory/      # Raw JSON data from Spotify export
├── app.py                 # Streamlit dashboard (main entry point)
├── data_loader.py         # Data loading and preprocessing
├── pyproject.toml         # uv project config
└── AGENTS.md              # This file
```

### Running the App
```bash
uv run streamlit run app.py
```

### Key Features
- **Dashboard**: Top albums, top artists, top tracks (by plays AND by minutes), most skipped tracks, one-hit wonders (tracks played once, 2+ min, not on playlist), not-on-playlist analysis (most played tracks you haven't saved)
- **Search**: Look up any track/artist with per-artist heatmaps showing listening patterns
- **Playlists**: Deep playlist analysis - sizes, top artists per playlist, track overlap detection (find tracks that appear in other playlists), playlist comparison, cross-playlist insights (shared artists/tracks)

### Data Sources

#### Streaming History (`Streaming_History_Audio_*.json`)
Extended streaming history with play-by-play data:
- `ts` - Timestamp (ISO 8601)
- `master_metadata_track_name` - Track name
- `master_metadata_album_artist_name` - Artist
- `master_metadata_album_album_name` - Album
- `ms_played` - Duration played in milliseconds
- `skipped` - Whether track was skipped
- `platform` - Device/platform used

#### Playlists (`Playlist1.json`)
User playlists with tracks:
- `playlists[].name` - Playlist name
- `playlists[].items[].track` - Track info (trackName, artistName, albumName, trackUri)
- `playlists[].collaborators` - Playlist collaborators

### Future Considerations
- Digital signage deployment (auto-refresh, kiosk mode)
- Additional visualizations as needed

---

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

