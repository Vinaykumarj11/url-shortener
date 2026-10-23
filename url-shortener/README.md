# URL Shortener API

A production-style URL shortening service built with **FastAPI**, **PostgreSQL**, and **Redis**. It covers what a real backend service needs: input validation, collision-safe code generation, read-through caching, per-client rate limiting, link expiry, click analytics, containerization, and CI.

![CI](https://github.com/<your-username>/url-shortener/actions/workflows/ci.yml/badge.svg)

## Features

- **Short links** with random base62 codes or a custom alias
- **Fast redirects** through a Redis read-through cache (Postgres stays the source of truth)
- **Rate limiting** per client IP with a Redis fixed-window counter, returning `429` with `Retry-After`
- **Expiring links**, and cache TTLs that never outlive the link
- **Click counting** with an atomic SQL increment, so concurrent redirects never lose updates
- **Interactive docs** at `/docs` (Swagger) and `/redoc`
- **Docker Compose** stack and **GitHub Actions** CI (lint, tests, image build)

## Architecture

```
            ┌──────────────┐
 client ──▶ │   FastAPI    │ ──▶ Redis   (redirect cache, rate-limit counters)
            │  (uvicorn)   │
            └──────┬───────┘
                   ▼
              PostgreSQL     (links, click counts, expiry)
```

On `GET /{code}` the service checks Redis first. On a miss it loads the link from Postgres, checks expiry, caches the target, and then redirects.

## Quick start

```bash
docker compose up --build
```

The API is then at http://localhost:8000 and the docs at http://localhost:8000/docs.

### Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # point at your local Postgres and Redis
uvicorn app.main:app --reload
```

## API

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/links` | Create a short link (rate limited) |
| `GET` | `/{code}` | Redirect to the target URL (307) |
| `GET` | `/api/v1/links/{code}` | Link details and click count |
| `DELETE` | `/api/v1/links/{code}` | Delete a link and evict its cache entry |
| `GET` | `/health` | Health check |

### Example

```bash
curl -X POST localhost:8000/api/v1/links \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "custom_code": "gh", "expires_at": "2030-01-01T00:00:00Z"}'
```

```json
{
  "code": "gh",
  "short_url": "http://localhost:8000/gh",
  "target_url": "https://github.com/",
  "clicks": 0,
  "created_at": "2026-10-23T02:57:41Z",
  "expires_at": "2030-01-01T00:00:00Z"
}
```

## Configuration

All settings are environment variables (see `.env.example`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | local Postgres | SQLAlchemy connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Cache and rate-limit store |
| `BASE_URL` | `http://localhost:8000` | Used to build `short_url` |
| `CODE_LENGTH` | `7` | Length of generated codes (62^7 ≈ 3.5 trillion) |
| `CACHE_TTL_SECONDS` | `3600` | Redirect cache TTL |
| `RATE_LIMIT_REQUESTS` | `20` | Requests allowed per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Window length |

## Testing

```bash
pytest -q
ruff check . && ruff format --check .
```

Tests use SQLite and `fakeredis`, so they run without any external services.

## Design decisions

- **Random codes instead of sequential IDs**, so links can't be enumerated. Collisions are retried on the database's unique constraint instead of being pre-checked, which avoids a race between check and insert.
- **Cache only the target URL**, not the whole record, so click counts stay accurate in Postgres.
- **Fixed-window rate limiting** keeps things simple. A sliding window or token bucket would be the next step for smoother limits.

## Roadmap

- [ ] Alembic migrations
- [ ] API keys and per-user link ownership
- [ ] Click analytics by day, referrer, and country
- [ ] Deploy to AWS with Terraform and GitHub Actions
