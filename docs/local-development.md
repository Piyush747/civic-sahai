# Local development

PostgreSQL is the only application database. Start it with `docker compose up -d postgres`, copy `backend/.env.example` to `backend/.env`, then run `alembic upgrade head` and `python -m app.seed`. Start the API with `uvicorn app.main:app --reload`.

Cloud Run deployment should build `backend/Dockerfile`, configure PostgreSQL/Cloud SQL connectivity and secrets, and run `alembic upgrade head` separately. Do not run migrations automatically on application startup or commit credentials.

