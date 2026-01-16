"""
Analytics API router - User dashboard and statistics
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from src.models.database import (
    User, LearningMaterial, QuizResult, NewsArticleDB,
    get_db
)
from src.logger import setup_logger

logger = setup_logger("daip.api.analytics")

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Get user dashboard with statistics"""
    # Learning materials stats
    total_materials = db.query(LearningMaterial).filter_by(user_id=user_id).count()
    completed_materials = db.query(LearningMaterial).filter_by(
        user_id=user_id,
        is_completed=True
    ).count()

    # Quiz stats
    quiz_results = db.query(QuizResult).filter_by(user_id=user_id).all()
    total_quizzes = len(quiz_results)
    correct_quizzes = sum(1 for r in quiz_results if r.is_correct)
    quiz_accuracy = (correct_quizzes / total_quizzes * 100) if total_quizzes > 0 else 0

    # Study time estimation
    materials = db.query(LearningMaterial).filter_by(user_id=user_id).all()
    total_study_time = sum(m.estimated_time for m in materials)

    # Recent activity
    recent_materials = db.query(LearningMaterial).filter_by(
        user_id=user_id
    ).order_by(LearningMaterial.created_at.desc()).limit(5).all()

    return {
        "learning_stats": {
            "total_materials": total_materials,
            "completed_materials": completed_materials,
            "in_progress": total_materials - completed_materials,
            "completion_rate": round(
                (completed_materials / total_materials * 100) if total_materials > 0 else 0,
                2
            )
        },
        "quiz_stats": {
            "total_quizzes": total_quizzes,
            "correct_answers": correct_quizzes,
            "accuracy": round(quiz_accuracy, 2),
            "average_time": sum(r.time_taken for r in quiz_results) / total_quizzes if total_quizzes > 0 else 0
        },
        "study_time": {
            "total_minutes": total_study_time,
            "total_hours": round(total_study_time / 60, 2)
        },
        "recent_activity": [
            {
                "id": m.id,
                "title": m.title,
                "type": m.material_type,
                "created_at": m.created_at
            }
            for m in recent_materials
        ]
    }


@router.get("/progress")
async def get_learning_progress(
    user_id: int = 1,  # TODO: Get from authentication
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get learning progress over time"""
    start_date = datetime.now() - timedelta(days=days)

    # Materials created per day
    materials_by_day = db.query(
        func.date(LearningMaterial.created_at).label('date'),
        func.count(LearningMaterial.id).label('count')
    ).filter(
        LearningMaterial.user_id == user_id,
        LearningMaterial.created_at >= start_date
    ).group_by(func.date(LearningMaterial.created_at)).all()

    # Quiz performance by day
    quiz_by_day = db.query(
        func.date(QuizResult.attempted_at).label('date'),
        func.count(QuizResult.id).label('total'),
        func.sum(func.cast(QuizResult.is_correct, type_=db.Integer)).label('correct')
    ).filter(
        QuizResult.user_id == user_id,
        QuizResult.attempted_at >= start_date
    ).group_by(func.date(QuizResult.attempted_at)).all()

    return {
        "period": {
            "start": start_date.date().isoformat(),
            "end": datetime.now().date().isoformat(),
            "days": days
        },
        "materials_created": [
            {"date": str(row.date), "count": row.count}
            for row in materials_by_day
        ],
        "quiz_performance": [
            {
                "date": str(row.date),
                "total": row.total,
                "correct": row.correct or 0,
                "accuracy": round((row.correct or 0) / row.total * 100, 2) if row.total > 0 else 0
            }
            for row in quiz_by_day
        ]
    }


@router.get("/categories-stats")
async def get_category_stats(
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Get statistics by news category"""
    # Get materials with their news articles
    materials_with_news = db.query(
        NewsArticleDB.category,
        func.count(LearningMaterial.id).label('count')
    ).join(
        LearningMaterial,
        LearningMaterial.news_article_id == NewsArticleDB.id
    ).filter(
        LearningMaterial.user_id == user_id
    ).group_by(NewsArticleDB.category).all()

    return {
        "categories": [
            {"category": row.category, "count": row.count}
            for row in materials_with_news
        ]
    }


@router.get("/streaks")
async def get_study_streaks(
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Get study streak information"""
    # Get all learning activity dates
    activity_dates = db.query(
        func.date(LearningMaterial.created_at).label('date')
    ).filter(
        LearningMaterial.user_id == user_id
    ).distinct().order_by(
        func.date(LearningMaterial.created_at).desc()
    ).all()

    if not activity_dates:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "total_active_days": 0
        }

    # Calculate current streak
    current_streak = 0
    today = datetime.now().date()
    for activity in activity_dates:
        activity_date = activity.date
        expected_date = today - timedelta(days=current_streak)

        if activity_date == expected_date:
            current_streak += 1
        else:
            break

    # Calculate longest streak
    longest_streak = 1
    current_count = 1

    for i in range(1, len(activity_dates)):
        prev_date = activity_dates[i-1].date
        curr_date = activity_dates[i].date

        if (prev_date - curr_date).days == 1:
            current_count += 1
            longest_streak = max(longest_streak, current_count)
        else:
            current_count = 1

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "total_active_days": len(activity_dates)
    }
