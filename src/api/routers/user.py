"""
User API router
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime

from src.models.database import User, Bookmark, get_db
from src.logger import setup_logger

logger = setup_logger("daip.api.user")

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str
    university: str
    major: str
    graduation_year: int


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    university: str
    major: str
    is_premium: bool

    class Config:
        from_attributes = True


class BookmarkCreate(BaseModel):
    news_article_id: int
    notes: str = ""


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create user (TODO: Hash password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=user_data.password,  # TODO: Hash this
        full_name=user_data.full_name,
        university=user_data.university,
        major=user_data.major,
        graduation_year=user_data.graduation_year
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/profile/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user profile"""
    user = db.query(User).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/bookmarks")
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Create a bookmark"""
    bookmark = Bookmark(
        user_id=user_id,
        news_article_id=bookmark_data.news_article_id,
        notes=bookmark_data.notes
    )

    db.add(bookmark)
    db.commit()

    return {"message": "Bookmark created", "bookmark_id": bookmark.id}


@router.get("/bookmarks")
async def get_bookmarks(
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Get user's bookmarks"""
    bookmarks = db.query(Bookmark).filter_by(user_id=user_id).all()

    return {
        "count": len(bookmarks),
        "bookmarks": bookmarks
    }


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: int,
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Delete a bookmark"""
    bookmark = db.query(Bookmark).filter_by(
        id=bookmark_id,
        user_id=user_id
    ).first()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    db.delete(bookmark)
    db.commit()

    return {"message": "Bookmark deleted"}
