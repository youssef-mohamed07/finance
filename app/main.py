"""
Main FastAPI application
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.api.endpoints import router
from app.exceptions import FinanceAnalyzerError
from app.models.responses import ErrorResponse, ErrorDetail
from app.services.audio_service import audio_processor
from app.services.transcription_service import transcription_service
from app.utils.file_utils import file_handler

# Setup logging
setup_logging()
logger = get_logger("main")

# Application startup time
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Finance Analyzer starting up...")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"Version: {settings.app_version}")
    
    yield
    
    logger.info("🛑 Finance Analyzer shutting down...")
    
    # Cleanup services
    try:
        await audio_processor.cleanup()
        await transcription_service.cleanup()
        await file_handler.cleanup_all()
        logger.info("✅ Cleanup completed successfully")
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered financial analysis from voice and text with production-ready security and performance",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add middleware (order matters!)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(router)


# Exception handlers
@app.exception_handler(FinanceAnalyzerError)
async def finance_analyzer_error_handler(request: Request, exc: FinanceAnalyzerError):
    """Handle custom application errors"""
    logger.warning(f"Application error: {exc.message}")
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details
            )
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    
    # Extract field information
    field = None
    if exc.errors():
        error = exc.errors()[0]
        if 'loc' in error and error['loc']:
            field = '.'.join(str(loc) for loc in error['loc'])
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid request data",
                field=field,
                details={"validation_errors": exc.errors()}
            )
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    # If detail is already a dict (from our endpoints), use it directly
    if isinstance(exc.detail, dict):
        error_detail = ErrorDetail(
            code=exc.detail.get("error", "HTTP_ERROR"),
            message=exc.detail.get("message", str(exc.detail)),
            details=exc.detail
        )
    else:
        error_detail = ErrorDetail(
            code="HTTP_ERROR",
            message=str(exc.detail)
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=error_detail).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    # Don't expose internal errors in production
    message = str(exc) if settings.debug else "An unexpected error occurred"
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message=message
            )
        ).dict()
    )


# Additional endpoints for monitoring
@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint"""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not found")
    
    from app.utils.cache import cache
    
    uptime = time.time() - app_start_time
    cache_stats = cache.stats()
    
    return {
        "uptime_seconds": uptime,
        "cache_stats": cache_stats,
        "settings": {
            "debug": settings.debug,
            "log_level": settings.log_level,
            "max_file_size_mb": settings.max_file_size / 1024 / 1024,
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True,
        reload=settings.debug
    )