# Civic SahAI

Civic SahAI is a citizen-facing civic complaint application with a React/Vite frontend and FastAPI/SQLAlchemy backend.

## Quick start

```bash
docker compose up -d postgres

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

Then, in another terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The API runs at `http://localhost:8000` and the frontend at `http://localhost:5173`. Local development uses PostgreSQL through the repository's Docker Compose service. Start it with `docker compose up -d postgres` before running migrations.

## Quality checks

```bash
cd backend && pytest && ruff check app tests
cd frontend && npm run typecheck && npm run lint && npm run test && npm run build
```

See [docs/architecture.md](docs/architecture.md), [docs/api-contracts.md](docs/api-contracts.md), and [docs/local-development.md](docs/local-development.md).

## Seed realistic MVP data

After applying migrations, run from `backend/`:

```bash
python -m app.seed_mvp
```

The script creates one Chennai city, its administrator, 34 citizens, zones, landmarks, 120 historic complaints grouped into 50 incidents, complaint image references, and resource-capacity/requirement/allocation records. It is idempotent by refusing to duplicate the dataset. For a disposable local database only, use `python -m app.seed_mvp --reset`.

The MVP seed uploads 40 deterministic placeholder civic-issue images to Filebase. To upload only the image objects, run `python -m app.seed_images` from `backend/`.

## Run incident clustering

The clustering worker consumes `complaint.received` events, filters compatible nearby incidents, and sends only the top K candidates to Gemini. If no candidates pass the algorithmic threshold, it creates an incident without an LLM call. It commits the Kafka offset only after the PostgreSQL transaction succeeds.

Configure `KAFKA_ENABLED=true`, `GEMINI_API_KEY`, and the Filebase credentials in `.env`, then run from `backend/`:

```bash
python -m app.workers.complaint_clustering_consumer
```

Apply migrations through head before starting the worker. That revision creates the full schema, including `uq_incident_complaints_complaint_id`, so a complaint can be linked to only one incident:

```bash
alembic upgrade head
```

