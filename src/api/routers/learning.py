"""
Learning Materials API router
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.models.database import LearningMaterial, get_db
from src.services.learning_service import get_learning_service
from src.services.news_scraper import NewsArticle
from src.logger import setup_logger

logger = setup_logger("daip.api.learning")

router = APIRouter()


class CreateMaterialRequest(BaseModel):
    news_article_id: int
    material_type: str = "summary"  # summary, quiz, flashcard
    difficulty_level: str = "intermediate"


class LearningMaterialResponse(BaseModel):
    id: int
    title: str
    content: str
    material_type: str
    difficulty_level: str
    estimated_time: int
    is_completed: bool

    class Config:
        from_attributes = True


@router.post("/create", response_model=LearningMaterialResponse)
async def create_learning_material(
    request: CreateMaterialRequest,
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Create learning material from news article"""
    try:
        service = get_learning_service()

        # Get news article
        from src.models.database import NewsArticleDB
        news_article = db.query(NewsArticleDB).filter_by(
            id=request.news_article_id
        ).first()

        if not news_article:
            raise HTTPException(status_code=404, detail="News article not found")

        # Convert to NewsArticle object
        article = NewsArticle(
            title=news_article.title,
            source=news_article.source,
            url=news_article.url,
            category=news_article.category,
            summary=news_article.summary,
            sentiment=news_article.sentiment,
            keywords=news_article.keywords
        )
        article.article_hash = news_article.article_hash

        # Create learning material
        material = service.create_learning_material(
            user_id=user_id,
            article=article,
            material_type=request.material_type,
            difficulty_level=request.difficulty_level
        )

        if not material:
            raise HTTPException(status_code=500, detail="Failed to create material")

        return material

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating learning material: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating learning material")


@router.get("/my-materials", response_model=List[LearningMaterialResponse])
async def get_my_materials(
    user_id: int = 1,  # TODO: Get from authentication
    material_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get user's learning materials"""
    query = db.query(LearningMaterial).filter_by(user_id=user_id)

    if material_type:
        query = query.filter_by(material_type=material_type)

    materials = query.order_by(LearningMaterial.created_at.desc()).all()
    return materials


@router.get("/daily-recommendations")
async def get_daily_recommendations(
    category: Optional[str] = None,
    limit: int = 10
):
    """Get daily recommended learning materials"""
    service = get_learning_service()
    materials = service.get_daily_learning_materials(category, limit)

    return {
        "date": "today",
        "count": len(materials),
        "materials": materials
    }


@router.patch("/{material_id}/complete")
async def mark_material_complete(
    material_id: int,
    db: Session = Depends(get_db)
):
    """Mark learning material as completed"""
    material = db.query(LearningMaterial).filter_by(id=material_id).first()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    material.is_completed = True
    db.commit()

    return {"message": "Material marked as completed", "material_id": material_id}
