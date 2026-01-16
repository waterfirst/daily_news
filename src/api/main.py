"""
FastAPI main application for DAIP Student Learning Platform
Backend API for news-based learning materials
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn

from src.config import settings
from src.logger import setup_logger
from src.api import routers

logger = setup_logger("daip.api")

# Create FastAPI app
app = FastAPI(
    title="DAIP Student Learning Platform API",
    description="AI-powered learning platform that converts news into educational materials",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("DAIP API starting up...")

    # Initialize database
    from src.models.database import get_db_manager
    db_manager = get_db_manager()
    db_manager.create_tables()

    logger.info("DAIP API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("DAIP API shutting down...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "DAIP Student Learning Platform API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",
            "ai": "available" if settings.anthropic_api_key else "unavailable"
        }
    }


# Include routers
app.include_router(routers.news_router, prefix="/api/news", tags=["News"])
app.include_router(routers.learning_router, prefix="/api/learning", tags=["Learning"])
app.include_router(routers.quiz_router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(routers.user_router, prefix="/api/users", tags=["Users"])
app.include_router(routers.analytics_router, prefix="/api/analytics", tags=["Analytics"])


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.now().isoformat()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run FastAPI server"""
    logger.info(f"Starting DAIP API server on {host}:{port}")
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)
