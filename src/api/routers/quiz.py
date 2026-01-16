"""
Quiz API router
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from src.models.database import Quiz, QuizResult, LearningMaterial, get_db
from src.logger import setup_logger

logger = setup_logger("daip.api.quiz")

router = APIRouter()


class QuizResponse(BaseModel):
    id: int
    question: str
    options: List[str]
    difficulty: str

    class Config:
        from_attributes = True


class SubmitQuizAnswer(BaseModel):
    quiz_id: int
    user_answer: str
    time_taken: int  # seconds


class QuizResultResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str


@router.get("/material/{material_id}", response_model=List[QuizResponse])
async def get_quizzes_for_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    """Get all quizzes for a learning material"""
    # Check if material exists
    material = db.query(LearningMaterial).filter_by(id=material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Learning material not found")

    quizzes = db.query(Quiz).filter_by(learning_material_id=material_id).all()

    return quizzes


@router.post("/submit", response_model=QuizResultResponse)
async def submit_quiz_answer(
    request: SubmitQuizAnswer,
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Submit quiz answer and get immediate feedback"""
    quiz = db.query(Quiz).filter_by(id=request.quiz_id).first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    is_correct = request.user_answer == quiz.correct_answer

    # Save result
    result = QuizResult(
        user_id=user_id,
        quiz_id=request.quiz_id,
        user_answer=request.user_answer,
        is_correct=is_correct,
        time_taken=request.time_taken,
        attempted_at=datetime.now()
    )

    db.add(result)
    db.commit()

    return QuizResultResponse(
        is_correct=is_correct,
        correct_answer=quiz.correct_answer,
        explanation=quiz.explanation
    )


@router.get("/stats")
async def get_quiz_stats(
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Get user's quiz statistics"""
    results = db.query(QuizResult).filter_by(user_id=user_id).all()

    total = len(results)
    correct = sum(1 for r in results if r.is_correct)
    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        "total_quizzes": total,
        "correct_answers": correct,
        "incorrect_answers": total - correct,
        "accuracy": round(accuracy, 2),
        "average_time": sum(r.time_taken for r in results) / total if total > 0 else 0
    }
