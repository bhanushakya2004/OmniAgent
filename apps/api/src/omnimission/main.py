"""FastAPI application factory, middleware configuration, and router mounting."""

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from omnimission.api.v1.auth import router as auth_router
from omnimission.api.v1.catalog import router as catalog_router
from omnimission.api.v1.missions import router as missions_router
from omnimission.api.v1.stores import router as stores_router
from omnimission.api.v1.uploads import router as uploads_router
from omnimission.api.v1.vision import router as vision_router
from omnimission.api.v1.voice import router as voice_router
from omnimission.core.config import get_settings
from omnimission.core.errors import ProblemDetail, ProblemException, problem_exception_handler
from omnimission.core.logging import get_logger, setup_logging
from omnimission.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager handling startup and shutdown events."""
    setup_logging()
    logger = get_logger("lifespan")
    logger.info("application_startup", app=app.title, version=app.version)
    yield
    logger.info("application_shutdown")
    await engine.dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="OmniMission AI API",
        version="0.1.0",
        description="FastAPI service for OmniMission AI - Multimodal Social-to-Shelf Commerce Engine",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and access logging middleware
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id

        # Skip logging for health endpoints
        if request.url.path not in ("/health", "/ready"):
            logger = get_logger("http")
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

        return response

    # Exception Handlers (RFC 7807 Problem Details)
    app.add_exception_handler(ProblemException, problem_exception_handler)  # type: ignore[arg-type]

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        errors = [
            {"loc": [str(loc) for loc in err["loc"]], "msg": err["msg"], "type": err["type"]}
            for err in exc.errors()
        ]
        problem = ProblemDetail(
            type="https://omnimission.ai/errors/validation-error",
            title="Request Validation Failed",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The request payload failed schema validation",
            code="VALIDATION_ERROR",
            request_id=request_id,
            errors=errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=problem.model_dump(exclude_none=True),
            media_type="application/problem+json",
        )

    # Liveness and Readiness Probes
    @app.get("/health", tags=["Health"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        """Simple liveness probe."""
        return {"status": "ok"}

    @app.get("/ready", tags=["Health"], summary="Readiness probe")
    async def readiness() -> dict[str, str]:
        """Readiness probe verifying database connectivity."""
        from sqlalchemy import text

        from omnimission.db.session import async_session_factory

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}

    # Static files mounting for uploads
    upload_dir = Path(settings.local_storage_path).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    # Mount API routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(stores_router, prefix="/api/v1")
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(missions_router, prefix="/api/v1")
    app.include_router(uploads_router, prefix="/api/v1")
    app.include_router(voice_router, prefix="/api/v1")
    app.include_router(vision_router, prefix="/api/v1")

    return app


app = create_app()
