"""
Database models for Daily Automated Intelligence Platform (DAIP)
Student Learning Platform integration
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.pool import StaticPool

from src.config import settings
from src.logger import setup_logger

logger = setup_logger("daip.database")

Base = declarative_base()


class User(Base):
    """User model for student accounts"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    university = Column(String)
    major = Column(String)
    graduation_year = Column(Integer)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    learning_materials = relationship("LearningMaterial", back_populates="user")
    quiz_results = relationship("QuizResult", back_populates="user")
    bookmarks = relationship("Bookmark", back_populates="user")


class NewsArticleDB(Base):
    """Stored news articles"""
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source = Column(String)
    url = Column(String, unique=True)
    category = Column(String, index=True)
    content = Column(Text)
    summary = Column(Text)
    sentiment = Column(String)
    keywords = Column(JSON)  # List of keywords
    published_at = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    article_hash = Column(String, unique=True, index=True)

    # Relationships
    learning_materials = relationship("LearningMaterial", back_populates="news_article")
    bookmarks = relationship("Bookmark", back_populates="news_article")


class LearningMaterial(Base):
    """Learning materials generated from news"""
    __tablename__ = "learning_materials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    news_article_id = Column(Integer, ForeignKey("news_articles.id"))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    difficulty_level = Column(String)  # beginner, intermediate, advanced
    estimated_time = Column(Integer)  # minutes
    material_type = Column(String)  # summary, detailed, quiz, flashcard
    tags = Column(JSON)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="learning_materials")
    news_article = relationship("NewsArticleDB", back_populates="learning_materials")
    quizzes = relationship("Quiz", back_populates="learning_material")


class Quiz(Base):
    """Quizzes generated from learning materials"""
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    learning_material_id = Column(Integer, ForeignKey("learning_materials.id"))
    question = Column(Text, nullable=False)
    options = Column(JSON)  # List of answer options
    correct_answer = Column(String, nullable=False)
    explanation = Column(Text)
    difficulty = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    learning_material = relationship("LearningMaterial", back_populates="quizzes")
    results = relationship("QuizResult", back_populates="quiz")


class QuizResult(Base):
    """Student quiz results"""
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    user_answer = Column(String)
    is_correct = Column(Boolean)
    time_taken = Column(Integer)  # seconds
    attempted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="quiz_results")
    quiz = relationship("Quiz", back_populates="results")


class Bookmark(Base):
    """User bookmarks for news and materials"""
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    news_article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="bookmarks")
    news_article = relationship("NewsArticleDB", back_populates="bookmarks")


class ETFAnalysisDB(Base):
    """Stored ETF analysis results"""
    __tablename__ = "etf_analyses"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    name = Column(String)
    current_price = Column(Float)
    change_pct = Column(Float)
    volume = Column(Integer)
    stochastic_k = Column(Float)
    stochastic_d = Column(Float)
    signal = Column(String)  # BUY, SELL, HOLD, WATCH
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)


class GeneratedContentDB(Base):
    """Stored generated content"""
    __tablename__ = "generated_contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String, index=True)  # blog, newsletter, report, column
    category = Column(String, index=True)
    summary = Column(Text)
    word_count = Column(Integer)
    tags = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)


# Database engine and session management
class DatabaseManager:
    """Database manager for DAIP"""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager"""
        self.database_url = database_url or settings.database_url

        # Create engine
        if self.database_url.startswith("sqlite"):
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(self.database_url)

        logger.info(f"Database initialized: {self.database_url}")

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")

    def get_session(self) -> Session:
        """Get database session"""
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        return SessionLocal()


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        _db_manager.create_tables()
    return _db_manager


def get_db() -> Session:
    """Get database session (for FastAPI dependency)"""
    db_manager = get_db_manager()
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()


# Example usage
if __name__ == "__main__":
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.create_tables()

    # Create a session
    session = db_manager.get_session()

    # Example: Create a test user
    test_user = User(
        email="test@university.edu",
        username="teststudent",
        hashed_password="hashed_pw_here",
        full_name="Test Student",
        university="Seoul National University",
        major="Computer Science",
        graduation_year=2026
    )

    session.add(test_user)
    session.commit()

    logger.info(f"Created test user: {test_user.username}")

    session.close()
