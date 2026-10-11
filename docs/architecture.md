# Architecture

The backend is a modular monolith. FastAPI endpoints translate HTTP into typed service calls; services own use-case rules; repositories own SQLAlchemy queries; models own persistence mapping. The frontend keeps API calls in feature modules and renders pages from typed query/mutation hooks.

PostgreSQL is both the local development and production operational store. Alembic is the schema-change mechanism in every environment.

`X-User-Id` is an optional MVP identifier, not authentication. The current listing is an explicitly public incident view containing only complaint fields intended for discovery; private-user reports require production authentication before exposure.

AI and Cloud Storage are intentionally integration boundaries and are not invoked in complaint creation.

