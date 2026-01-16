"""
News API router - Get news articles and summaries
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session

from src.models.database import NewsArticleDB, get_db
from src.logger import setup_logger

logger = setup_logger("daip.api.news")

router = APIRouter()


# Pydantic models
class NewsArticleResponse(BaseModel):
    id: int
    title: str
    source: str
    url: str
    category: str
    summary: Optional[str]
    sentiment: str
    keywords: Optional[List[str]]
    published_at: Optional[datetime]
    scraped_at: datetime

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    total: int
    articles: List[NewsArticleResponse]
    page: int
    page_size: int


@router.get("/", response_model=NewsListResponse)
async def get_news_articles(
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get news articles with pagination and filters

    - **category**: Filter by category (IT, 경제, etc.)
    - **sentiment**: Filter by sentiment (positive, negative, neutral)
    - **page**: Page number (starts from 1)
    - **page_size**: Items per page (max 100)
    """
    try:
        query = db.query(NewsArticleDB)

        # Apply filters
        if category:
            query = query.filter(NewsArticleDB.category == category)

        if sentiment:
            query = query.filter(NewsArticleDB.sentiment == sentiment)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        articles = query.order_by(
            NewsArticleDB.scraped_at.desc()
        ).offset(offset).limit(page_size).all()

        return NewsListResponse(
            total=total,
            articles=articles,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching news articles")


@router.get("/{article_id}", response_model=NewsArticleResponse)
async def get_news_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific news article by ID"""
    article = db.query(NewsArticleDB).filter(NewsArticleDB.id == article_id).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article


@router.get("/categories/list")
async def get_categories(db: Session = Depends(get_db)):
    """Get list of available news categories"""
    try:
        categories = db.query(NewsArticleDB.category).distinct().all()
        return {
            "categories": [cat[0] for cat in categories if cat[0]]
        }

    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching categories")


@router.get("/trending/today")
async def get_trending_news(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get trending news from today"""
    try:
        today = datetime.now().date()

        articles = db.query(NewsArticleDB).filter(
            NewsArticleDB.scraped_at >= today
        ).order_by(
            NewsArticleDB.scraped_at.desc()
        ).limit(limit).all()

        return {
            "date": today.isoformat(),
            "count": len(articles),
            "articles": articles
        }

    except Exception as e:
        logger.error(f"Error fetching trending news: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching trending news")
