# NFL Key Numbers Widget

Frequency analysis of margins of victory and total points across NFL history (1999–present), using the [nflverse](https://github.com/nflverse/nflverse-data) `schedules` data release.

## Files

- `index.html` — the widget (single self-contained file with embedded data)
- `template.html` — the source template before data injection
- `games_data.json` — extracted dataset (kept in repo for transparency)
- `build.py` — pulls latest nflverse data, generates JSON, rebuilds `index.html`
- `.github/workflows/update-data.yml` — runs `build.py` weekly

## Deploy to GitHub Pages

1. Push everything to a repo (e.g., `nfl-key-numbers`)
2. Settings → Pages → Source: `main` branch, root folder
3. Visit `https://[your-username].github.io/nfl-key-numbers/`

## Auto-update from nflverse

The included GitHub Action runs every Tuesday at 13:00 UTC (early morning Eastern, after Monday Night Football finalizes). It pulls the latest `games.csv` from the nflverse `schedules` release, regenerates `games_data.json` and `index.html`, and commits the changes.

### One-time setup

1. Confirm Settings → Actions → General → "Workflow permissions" is set to **Read and write permissions** (this allows the bot to commit back).
2. Move `update-data.yml` into `.github/workflows/` in your repo (the directory has to exist).
3. To test immediately, go to Actions → "Update NFL Data" → "Run workflow" — it triggers a manual run.

### Manual rebuild

```bash
python build.py
```

Pulls the latest data, regenerates everything. No external dependencies — uses only the Python standard library.

## Embed in Action Network articles

```html
<iframe
  src="https://[your-username].github.io/nfl-key-numbers/"
  width="100%"
  height="1100"
  frameborder="0"
  scrolling="no"
  style="border:0; max-width:1280px;">
</iframe>
```

Mobile articles will need taller iframes (~1500px) since filters wrap.

## Features

- **Two views** — Margin of Victory (spread relevance) and Total Points (over/under relevance)
- **Filters**:
  - Season range (dual-handle slider)
  - Spread range (absolute, 0 → 21+)
  - Game type (All / Regular / Postseason)
  - **Period comparison** — toggle on to compare two season ranges side-by-side
- **Stats strip** — most common, top 3, median, sample size; recalculates per filter
- **Smart label collision avoidance** — bar labels and x-axis ticks de-collide automatically as data density changes

## Filter behavior

- Spread filter operates on the closing line, not the actual margin. "0–3" filters games priced as toss-ups to FG-favorites.
- Spread upper handle at 21 includes all blowouts (21+).
- Period A and Period B can overlap in compare mode (Period B defaults to most recent ~half).

## Data shape

Each record is `[season, game_type, abs_margin, total_points, abs_spread]`:
- `game_type`: 0 = regular season, 1 = playoff (any round)
- `abs_margin`: |home_score − away_score|
- `abs_spread`: |closing_spread_line|, rounded to nearest 0.5
