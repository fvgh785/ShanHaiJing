# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

《山海经》视频制作全流程留痕系统 — a full-stack workflow tracking and AI-assisted production system for a solo video creator making "Classic of Mountains and Seas" mythological creature videos. Flask calls DeepSeek API directly for prompt generation and style review.

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | Vue 3 + Naive UI + Vite | Vue 3.4+, Naive UI 2.x, Vite 5.x |
| Backend | Flask + SQLAlchemy | Flask 3.x, SQLAlchemy 2.x |
| Database | SQLite (WAL mode) | 3.x |
| Migrations | Alembic (Flask-Migrate) | — |
| AI Model | DeepSeek API (deepseek-chat) | — |
| Web Server | Nginx | 1.25+ |
| SSL | Let's Encrypt (Certbot) | — |
| Deployment | Docker + Docker Compose | — |
| Python Deps | uv | latest |
| Target OS | Alibaba Cloud Linux 3 (RHEL-based) | — |

## Architecture

```
Browser (PWA) → Nginx (SSL + static files) → Flask REST API
                                                  ├── DeepSeek API (prompt generation + style review)
                                                  └── SQLite + File System
```

### Backend Layers

1. **REST API layer**: Plan management, production record CRUD, data import/export
2. **Business logic layer**: Scheduling engine, points/quota tracking, export service
3. **AI client layer** (`deepseek_client.py`): Direct DeepSeek API calls with retry logic and circuit breaker

### Core Domain Concepts

- **Plans** (`plans` table): Scheduled production tasks — creature name, priority (1-5), planned date, recommended tool, status (pending/in_progress/completed/cancelled)
- **Records** (`records` table): The central entity — each record captures a full production cycle: task binding → AI prompt generation → output association → review. Tracks prompts (image/video/negative), style review scores, points consumed, output URLs, notes
- **Harmony Baselines** (`harmony_baselines` table): User-curated "perfect template" style baselines stored as Markdown files with YAML frontmatter. Define the visual anchor for the video series (lighting, composition, color, detail specs). Version-controlled with activation/deactivation
- **Hermes Logs** (`hermes_logs` table): Full audit trail of every DeepSeek API call — system prompt, user input, response, tokens, cost, duration, adoption status
- **Daily Quotas** (`daily_quotas` table): Per-tool daily usage tracking (Jimeng AI ~100/day, Seedance ~130/day)

### Key Workflow (Plan → Publish)

1. User views today's plan → clicks "Start Production"
2. User selects creature + style → Flask sends structured request to DeepSeek API
3. DeepSeek returns image prompt + video prompt (optionally referencing active Harmony baseline)
4. (Optional) Flask calls DeepSeek for style consistency check against baseline, returns 4-dimension score + suggestions
5. User reviews/edits/adopts prompts → saves record
6. User manually generates images/video in external tools (Jimeng/Seedance)
7. User returns to fill in output URLs + review notes → record updated

### Directory Structure

```
/
├── backend/                  # Flask application
│   ├── app/
│   │   ├── api/              # REST API blueprints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic (scheduling, quotas, export)
│   │   └── hermes_client/    # Retry/circuit-breaker utilities (deepseek_client.py at app level)
│   ├── migrations/           # Alembic migration scripts
│   └── backups/              # Automated SQLite backups
├── frontend/                 # Vue 3 + Vite application
│   ├── src/
│   │   ├── views/            # Page-level components
│   │   ├── components/       # Reusable components
│   │   ├── api/              # Axios API client layer
│   │   └── stores/           # Pinia state stores
│   └── public/               # Static assets, service worker
├── hermes/                   # Reference skill files (prompt templates, no longer deployed)
│   └── skills/               # Original skill .md files (now inlined in deepseek_client.py)
├── nginx/                    # Nginx configuration
├── docker-compose.yml
└── prd.md
```

## Commands

### Backend (Flask)

```bash
# Install dependencies
cd backend && uv sync

# Run development server
flask run --debug

# Database migrations
flask db migrate -m "description"
flask db upgrade

# Run tests
pytest
pytest tests/test_api.py -v  # single test file
pytest -k "test_create_record"  # single test by name
```

### Frontend (Vue 3 + Vite)

```bash
cd frontend && npm install

# Development server with HMR
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

### Docker

```bash
# Start Flask service
docker compose up -d

# View logs
docker compose logs -f flask

# Rebuild after changes
docker compose build && docker compose up -d
```

### Database

```bash
# Manual backup
sqlite3 data/app.db ".backup backups/backup_$(date +%Y%m%d).db"
```

## Key Design Decisions

1. **SQLite over PostgreSQL**: Single-user scenario; simpler backup (single file copy); zero-config
2. **Flask over FastAPI**: More mature SQLAlchemy integration docs; sufficient for single-user REST API
3. **Vue 3 over React**: Flatter learning curve for solo iteration
4. **Local-first data sovereignty**: Cloud SQLite for operational use; JSON export for offline backup and cross-server portability
5. **Direct DeepSeek API calls**: Flask calls DeepSeek directly instead of through a separate agent process — simpler deployment, fewer moving parts, same retry/circuit-breaker resilience
6. **Harmony baselines are Markdown files**: Human-readable, version-controllable, editable outside the app

## API Design

- Prefix: `/api/v1/` (URL path versioning)
- Error format: `{"error": {"code": "ERROR_CODE", "message": "..."}}`
- Pagination: `{"data": [...], "pagination": {"page": 1, "per_page": 20, "total": 127}}`
- 7 resource groups: `/plans`, `/records`, `/hermes`, `/baselines`, `/data`, `/health`, `/stats`
- See prd.md Section 5 for full endpoint table

## Error Handling & Resilience

- **DeepSeek API**: 3 retries with exponential backoff (1s/2s/4s), 30s timeout → degrade to manual input mode → circuit-break after 5 consecutive failures (60s cooldown)
- **DeepSeek unavailable**: `/health` returns unconfigured status; frontend shows "skip AI" path; core CRUD remains functional
- **Database**: all writes wrapped in transactions; auto-backup before migrations
- **Docker**: `restart: unless-stopped` on Flask service

## Docker Resource Limits (1C/1G)

| Container | Memory Limit | Key Config |
|-----------|-------------|------------|
| Nginx | 64MB | alpine image (host) |
| Flask | 256MB | gunicorn -w 1 --threads 2 |

Single Flask container, leaving ~700MB for OS, Docker daemon, and file cache.

## Development Phases

- **Phase 1 (Week 1) MVP**: Plans/Records CRUD + prompt generation (no style review) + dashboard + Docker deploy. Explicitly excludes: Harmony baselines, style review, data export/import, auto-backup, statistics, PWA.
- **Phase 2 (Week 2)**: Harmony baselines + style review + record detail page + mobile responsive
- **Phase 3 (Week 3)**: Data export/import + auto-backup + statistics panel + PWA

## Important Constraints

- **Single user only**: No multi-tenancy, no concurrent write contention
- **DeepSeek API budget**: Monthly cap ~50 RMB; leverage free tier
- **All AI calls go through `deepseek_client.py`**: Centralized retry, circuit breaker, and audit logging
- **Data backup dual strategy**: Automated server-side backup (cron daily at 03:00) + manual JSON export from frontend
- **External tools are manual**: The system does NOT integrate with Jimeng/Seedance APIs — user copies prompts manually, returns to log results
- **Data model note**: `records.hermes_request_id` removed (v4.0); `hermes_logs.record_id` is the reverse link. All FK constraints explicitly declared.
