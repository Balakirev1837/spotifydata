# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Beads Workflow (REQUIRED)

**All work MUST be tracked with beads.** This ensures work persists across sessions and enables multi-session project management.

### When to Use Beads
- **Features**: Any new functionality (`bd create --type=feature`)
- **Bugs**: Issues to fix (`bd create --type=bug`)
- **Tasks**: General work items (`bd create --type=task`)
- **Multi-step work**: Anything requiring multiple sessions
- **Discovered work**: Issues found while working on something else

### Session Start
```bash
bd prime              # Load context (auto-runs via hooks)
bd ready              # Find available work
bd show <id>          # Review issue details before starting
bd update <id> --status=in_progress  # Claim work
```

### During Work
- Create issues for discovered work: `bd create --title="..." --type=task --priority=2`
- Add dependencies when needed: `bd dep add <issue> <depends-on>`
- Priority scale: 0=critical, 1=high, 2=medium, 3=low, 4=backlog

### Session End (MANDATORY)
```bash
git status              # Check changes
git add <files>         # Stage code
bd sync                 # Sync beads
git commit -m "..."     # Commit code
bd sync                 # Sync any new beads changes
git push                # MUST push - work isn't done until pushed
```

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
- **Genres**: Genre breakdown and trends (requires Spotify API credentials - see SPOTIFY_API.md)

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

### Spotify API Integration (Optional)

For genre analysis, the app can fetch artist genres from the Spotify Web API.
See `SPOTIFY_API.md` for full documentation.

**Quick setup:**
1. Create app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Set environment variables:
   ```
   SPOTIFY_CLIENT_ID=your_id
   SPOTIFY_CLIENT_SECRET=your_secret
   ```
3. Restart app - genres will be fetched and cached automatically

**Files:**
- `spotify_api.py` - API authentication and fetching
- `.cache/artist_genres.json` - Cached genre data (gitignored)

### Future Considerations
- Digital signage deployment (auto-refresh, kiosk mode)
- Additional visualizations as needed

---

## Quick Reference

See "Beads Workflow" section above for detailed bd commands.

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

