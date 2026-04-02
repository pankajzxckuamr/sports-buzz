# Sports Buzz + AthleteX — Integrated Project

> A real sports data pipeline: a Python web crawler that tracks player
> mentions across the sports internet, connected to a React frontend
> that visualises buzz scores, trending athletes, and crawled articles.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Full Stack Overview                          │
│                                                                  │
│  Python Backend (sportsbuzz/)        React Frontend (athletepulse2/)
│  ─────────────────────────────       ──────────────────────────── │
│  crawler.py  ──► parser.py           services/api.js             │
│      │              │                   │  (tries crawler first) │
│      ▼              ▼                   ▼                        │
│  browser.py  ──► database.py        services/dataAdapter.js      │
│  (fetch URLs)    (SQLite)              │  (maps shapes)          │
│                     │                  ▼                         │
│               api.py :8081  ◄─────  components/                  │
│               (REST JSON)            BuzzLeaderboard             │
│                                      CrawlerStatusBar            │
│                                      PostCard (real articles)    │
│                                      PlayerProfile               │
│                                      TrendingPanel               │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Sports websites  →  crawler.py (BFS)  →  parser.py  →  SQLite DB
                                                            │
                                                       api.py :8081
                                                            │
                                                     React frontend
                                                   (shows live data
                                                    or mock fallback)
```

---

## Project Structure

```
sports-buzz/
├── sportsbuzz/               ← Python crawler + API
│   ├── run.py                ← Unified launcher (start here)
│   ├── crawler.py            ← BFS web crawler engine
│   ├── api.py                ← REST API server (port 8081)
│   ├── database.py           ← SQLite schema + helpers
│   ├── parser.py             ← HTML parser, mention detection, sentiment
│   ├── players_seed.py       ← 38 athletes + 19 sources
│   ├── browser.py            ← HTTP fetcher (your custom browser)
│   ├── dns_resolver.py       ← Raw DNS resolver
│   └── sports_buzz.db        ← SQLite database (created on setup)
│
└── athletepulse2/            ← React frontend (AthleteX)
    └── src/
        ├── services/
        │   ├── api.js          ← Calls crawler API, falls back to mock
        │   └── dataAdapter.js  ← Maps Python shapes → frontend shapes
        ├── components/
        │   ├── BuzzLeaderboard.jsx   ← Live buzz rankings from crawler
        │   └── CrawlerStatusBar.jsx  ← Online/offline indicator
        └── pages/
            └── Dashboard.jsx   ← Integrated dashboard
```

---

## Quick Start

### 1. Set up the database (once)
```bash
cd sportsbuzz
python run.py setup
```
Seeds 38 players and 19 sports sources.

### 2. Start the API server
```bash
python run.py api
# → http://localhost:8081
```

### 3. Start the React frontend (new terminal)
```bash
cd athletepulse2
npm install    # first time only
npm run dev
# → http://localhost:5173
```
The frontend will show the **"Crawler Online"** badge and load real data.

### 4. Run a crawl to populate data (new terminal)
```bash
cd sportsbuzz
python run.py crawl
# or just one sport:
python run.py crawl --sport Cricket
```

### 5. Check what's been collected
```bash
python run.py status
python run.py buzz
```

### 6. Production: API + auto-crawl together
```bash
python run.py all
```

---

## How the Integration Works

### Automatic fallback

The React frontend **always works**, even with no backend:

```
api.js calls crawler  →  success  →  show real data + "Live" badge
                      →  timeout  →  silently use mock data
```

No config needed. Open the frontend; if the API is running it auto-detects it.

### Data mapping

`dataAdapter.js` converts Python API shapes into what the components expect:

| Python API returns | Frontend receives |
|---|---|
| `{ name, sport, nationality, aliases }` | `{ name, sport, initials, avatarColor, buzzScore, stats }` |
| `{ title, url, summary, sentiment }` | `{ title, content, platform: "news", timestamp }` |
| `{ name, buzz_score, mention_count }` | `{ rank, name, buzzScore, mentionCount, avatarColor }` |

### New UI elements (only visible when crawler is online)

**CrawlerStatusBar** — slim bar at top of Dashboard:
- Green dot + "Crawler Online"
- Article count, mention count, articles today
- Top player of the day

**BuzzLeaderboard** — right panel on Dashboard:
- All players ranked by today's buzz score
- Filter by sport (tabs)
- Buzz bar visualisation per player
- Red "Mock data" badge when offline

---

## REST API Reference

All endpoints return JSON. CORS is enabled for `localhost:5173` and `localhost:3000`.

| Endpoint | Description |
|---|---|
| `GET /api/players?sport=Cricket` | All players, optionally filtered by sport |
| `GET /api/players/<id>/buzz?days=7` | Buzz history for one player |
| `GET /api/players/<id>/articles?limit=20` | Recent crawled articles mentioning player |
| `GET /api/players/<id>/trend?days=30` | Buzz trend data for charts |
| `GET /api/buzz/top?sport=Football&limit=10` | Top buzzing players today |
| `GET /api/buzz/leaderboard?sport=Cricket` | Full leaderboard, filterable by sport |
| `GET /api/search?q=Messi` | Search by name or nickname |
| `GET /api/stats` | Crawler health (article count, mentions, top player) |

---

## Buzz Score Formula

```
buzz = (mentions × 0.6) + (articles × 3 × 0.3) + ((sentiment + 1) × 5 × 0.1)
```
- Capped at 100
- Recomputed at the end of each crawl cycle
- Stored per player per day (visible as trend charts)

---

## Adding Players or Sources

Edit `players_seed.py`, then re-run setup:

```python
# In PLAYERS list:
("Player Name", "Sport", "Country", ["Nickname", "Short name"]),

# In SOURCES list:
("Site Name", "https://www.site.com", "Football", "news"),
```

```bash
python run.py setup
```

---

## Ports

| Service | Port | Command |
|---|---|---|
| React frontend (Vite dev) | 5173 | `npm run dev` (in athletepulse2/) |
| Crawler REST API | 8081 | `python run.py api` |
| Static file server | 8080 | `python server.py` |

---

## sports-data-backend integration (PostgreSQL pipeline)

The crawler can **push every fetched HTML page** to the Node **`sports-data-backend`** (`/v1/ingest/html`), where raw files are stored and the existing queue workers parse, dedupe, and enrich content.

1. Install Python deps: `pip install -r requirements.txt`
2. Copy `.env.example` → `.env` and set **`SPORTS_BACKEND_URL=http://localhost:3000`**
3. Start **sports-data-backend** (Postgres, Redis, `npm run dev`, `npm run worker`)
4. Run **`python run.py crawl`** as usual

### Website list (edit YAML, not only SQLite)

Add or remove sites in **`config/crawl_sites.yaml`**. When this file exists and at least one row has `enabled: true`, **only those `base_url`s** are crawled (synced into SQLite for local buzz). If you delete the file, the crawler falls back to **all sources** from `players_seed` / SQLite.

### Social JSON (X / YouTube / Instagram)

1. Edit **`config/social_accounts.yaml`** — enable rows and set handles / channel IDs / `ig_user_id`.
2. Put API keys in **`.env`** (see `.env.example`).
3. Run **`python run.py social`** — each item is POSTed to **`/v1/ingest/json`** for normalization and enrichment.

| Command | Purpose |
|--------|---------|
| `python run.py crawl` | BFS crawl → local SQLite + optional backend HTML ingest |
| `python run.py social` | API pulls → backend JSON ingest |

---

## Project layout (updated)

```
sportsbuzz/
  config/
    crawl_sites.yaml       ← websites to visit (editable list)
    social_accounts.yaml   ← X / YouTube / Instagram accounts
  social/                  ← API fetchers + run.py
  backend_client.py        ← POST to sports-data-backend
  config_loader.py         ← YAML → DB + crawl source resolution
```
