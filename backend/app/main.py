from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.router import router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title="Civic SahAI API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_allowed_origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.exception_handler(HTTPException)
async def http_error_handler(_request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> JSONResponse:
    return JSONResponse({"status": "ready"})

