"""
CampusFlow Backend — Application Entrypoint.

Initializes FastAPI, logging, error handlers, and core singletons (settings, JWT).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from fastapi.exceptions import RequestValidationError

from app.api.internal.scheduler import router as internal_scheduler_router
from app.api.internal.tasks import router as internal_tasks_router
from app.api.router import api_v1_router
from app.api.wellknown import router as wellknown_router
from app.core.config import get_settings
from app.core.exceptions import (
    CampusFlowError,
    campus_flow_exception_handler,
    generic_exception_handler,
    request_validation_exception_handler,
)
from app.core.limiter import limiter
from app.core.logging_config import configure_logging, get_logger
from app.core.security import init_jwt_manager
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import close_db_engine, get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    settings = get_settings()
    
    # 1. Logging
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    logger.info("Starting CampusFlow backend in %s mode", settings.app_env)

    # 2. JWT Manager
    init_jwt_manager(settings)
    
    # 3. DB Engine
    get_engine()
    
    yield
    
    # --- Shutdown ---
    logger.info("Shutting down CampusFlow backend")
    await close_db_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="College Placement Management Platform API",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # SlowAPI Rate Limiter
    app.state.limiter = limiter

    # Security Headers Middleware
    app.add_middleware(
        SecurityHeadersMiddleware,
        is_production=settings.app_env.lower() in ("production", "staging"),
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handling
    app.add_exception_handler(CampusFlowError, campus_flow_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Routers
    app.include_router(wellknown_router, prefix="/.well-known")
    app.include_router(api_v1_router, prefix="/api/v1")
    app.include_router(internal_tasks_router, prefix="/internal/tasks", tags=["Internal Tasks"])
    app.include_router(internal_scheduler_router, prefix="/internal/scheduler", tags=["Internal Scheduler"])

    return app



app = create_app()
