# Stitch — design + frontend

- **`velocity_dark/DESIGN.md`** — design system *The Kinetic Editorial* / *The Digital Arena* (colors, type, components).
- **`*/screen.png`** — reference frames for landing, feed, explore, player flows.
- **`web/`** — **Vite + React** UI that talks to **`../sports-data-backend`** (PostgreSQL + Redis + workers).

## Run the UI

1. Start the API (from `sports-data-backend`): `docker compose up -d`, `npm run db:migrate`, `npm run dev`, and in another terminal `npm run worker`.
2. From **`stitch/web`**: `npm install` then `npm run dev` (default [http://localhost:5173](http://localhost:5173)).

The dev server **proxies** `/v1` and `/health` to `http://localhost:3000`.

Production or custom API URL: set `VITE_API_BASE` (e.g. `https://api.example.com`) and ensure CORS allows your origin (the backend uses `@fastify/cors`).

## Screens

| Route | Backing API |
|-------|-------------|
| `/` | — |
| `/feed` | `GET /v1/trending`, `GET /v1/content/enriched` |
| `/explore` | `GET /v1/search` (if Elasticsearch) else `GET /v1/content/enriched?q=` |
| `/players` | `GET /v1/entities` |
| `/player/:name` | `GET /v1/content/by-entity/:name` |
| `/content/:id` | `GET /v1/content/:id` |

Data is read from the **same PostgreSQL** (and optional Elasticsearch) as the aggregation backend—not from the browser directly to the DB.
