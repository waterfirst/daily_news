"""
API routers for DAIP Student Learning Platform
"""
from src.api.routers.news import router as news_router
from src.api.routers.learning import router as learning_router
from src.api.routers.quiz import router as quiz_router
from src.api.routers.user import router as user_router
from src.api.routers.analytics import router as analytics_router

__all__ = [
    "news_router",
    "learning_router",
    "quiz_router",
    "user_router",
    "analytics_router"
]
