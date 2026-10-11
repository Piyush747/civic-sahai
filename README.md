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

