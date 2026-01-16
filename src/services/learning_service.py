"""
Learning Service for converting news into educational materials
AI-powered summaries, quizzes, and study materials for students
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import anthropic

from src.config import settings
from src.logger import setup_logger
from src.models.database import (
    get_db_manager,
    NewsArticleDB,
    LearningMaterial,
    Quiz,
    User
)
from src.services.news_scraper import NewsArticle

logger = setup_logger("daip.learning")


class LearningService:
    """Convert news articles into learning materials"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize learning service"""
        self.api_key = api_key or settings.anthropic_api_key
        if self.api_key:
            self.client = anthropic.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("Anthropic API key not configured")

        self.db_manager = get_db_manager()
        logger.info("Learning Service initialized")

    def generate_summary(
        self,
        article: NewsArticle,
        difficulty_level: str = "intermediate"
    ) -> str:
        """
        Generate educational summary from news article

        Args:
            article: News article to summarize
            difficulty_level: beginner, intermediate, advanced

        Returns:
            Generated summary
        """
        if not self.client:
            return "AI service not available"

        try:
            prompt = f"""당신은 대학생을 위한 교육 콘텐츠 작성자입니다. 다음 뉴스 기사를 {difficulty_level} 레벨의 학습 자료로 변환해주세요.

기사 제목: {article.title}
출처: {article.source}
카테고리: {article.category}

요구사항:
1. 핵심 내용 3-5개 불릿 포인트로 요약
2. 주요 개념 설명 (전문 용어 포함 시 쉽게 설명)
3. 실생활/학업 연관성 설명
4. 추가 학습 주제 제안

난이도: {difficulty_level}
- beginner: 고등학생도 이해 가능
- intermediate: 대학생 수준
- advanced: 전문적 분석 포함

학습 자료를 작성해주세요:"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text
            logger.info(f"Generated summary for: {article.title}")
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return ""

    def generate_quiz(
        self,
        article: NewsArticle,
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions from news article

        Args:
            article: News article
            num_questions: Number of questions to generate

        Returns:
            List of quiz questions
        """
        if not self.client:
            return []

        try:
            prompt = f"""당신은 교육 평가 전문가입니다. 다음 뉴스 기사를 바탕으로 {num_questions}개의 객관식 문제를 만들어주세요.

기사 제목: {article.title}
카테고리: {article.category}

요구사항:
1. 각 문제는 4개의 선택지
2. 정답은 명확해야 함
3. 오답도 그럴듯해야 함
4. 각 문제마다 해설 포함
5. 난이도 표시 (easy, medium, hard)

다음 JSON 형식으로 응답해주세요:
[
  {{
    "question": "질문 내용",
    "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
    "correct_answer": "선택지1",
    "explanation": "정답 해설",
    "difficulty": "medium"
  }}
]

문제를 생성해주세요:"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            import json
            import re

            content = response.content[0].text
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                quizzes = json.loads(json_match.group(0))
                logger.info(f"Generated {len(quizzes)} quiz questions")
                return quizzes
            else:
                logger.warning("Could not parse quiz JSON")
                return []

        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            return []

    def generate_flashcards(
        self,
        article: NewsArticle,
        num_cards: int = 10
    ) -> List[Dict[str, str]]:
        """
        Generate flashcards from article

        Args:
            article: News article
            num_cards: Number of flashcards

        Returns:
            List of flashcards (front/back)
        """
        if not self.client:
            return []

        try:
            prompt = f"""다음 뉴스 기사에서 {num_cards}개의 학습 플래시카드를 만들어주세요.

기사 제목: {article.title}
카테고리: {article.category}

JSON 형식으로 응답:
[
  {{
    "front": "질문 또는 용어",
    "back": "답변 또는 설명"
  }}
]

플래시카드를 생성해주세요:"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            import re

            content = response.content[0].text
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                flashcards = json.loads(json_match.group(0))
                logger.info(f"Generated {len(flashcards)} flashcards")
                return flashcards

            return []

        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            return []

    def create_learning_material(
        self,
        user_id: int,
        article: NewsArticle,
        material_type: str = "summary",
        difficulty_level: str = "intermediate"
    ) -> Optional[LearningMaterial]:
        """
        Create learning material from news article

        Args:
            user_id: User ID
            article: News article
            material_type: summary, quiz, flashcard
            difficulty_level: beginner, intermediate, advanced

        Returns:
            LearningMaterial object
        """
        session = self.db_manager.get_session()

        try:
            # Check if article exists in DB
            news_db = session.query(NewsArticleDB).filter_by(
                article_hash=article.article_hash
            ).first()

            if not news_db:
                # Create news article in DB
                news_db = NewsArticleDB(
                    title=article.title,
                    source=article.source,
                    url=article.url,
                    category=article.category,
                    summary=article.summary,
                    sentiment=article.sentiment,
                    keywords=article.keywords,
                    published_at=article.published_at,
                    article_hash=article.article_hash
                )
                session.add(news_db)
                session.commit()
                session.refresh(news_db)

            # Generate content based on type
            if material_type == "summary":
                content = self.generate_summary(article, difficulty_level)
                estimated_time = 5
            elif material_type == "quiz":
                quizzes = self.generate_quiz(article)
                content = f"Generated {len(quizzes)} questions"
                estimated_time = len(quizzes) * 2
            elif material_type == "flashcard":
                flashcards = self.generate_flashcards(article)
                content = f"Generated {len(flashcards)} flashcards"
                estimated_time = len(flashcards)
            else:
                content = "Unknown material type"
                estimated_time = 0

            # Create learning material
            material = LearningMaterial(
                user_id=user_id,
                news_article_id=news_db.id,
                title=f"{article.title} - {material_type.title()}",
                content=content,
                difficulty_level=difficulty_level,
                estimated_time=estimated_time,
                material_type=material_type,
                tags=article.keywords or []
            )

            session.add(material)
            session.commit()
            session.refresh(material)

            # If quiz type, also create quiz entries
            if material_type == "quiz":
                quizzes = self.generate_quiz(article)
                for q in quizzes:
                    quiz = Quiz(
                        learning_material_id=material.id,
                        question=q['question'],
                        options=q['options'],
                        correct_answer=q['correct_answer'],
                        explanation=q.get('explanation', ''),
                        difficulty=q.get('difficulty', 'medium')
                    )
                    session.add(quiz)

                session.commit()

            logger.info(f"Created learning material: {material.title}")
            return material

        except Exception as e:
            logger.error(f"Error creating learning material: {str(e)}")
            session.rollback()
            return None

        finally:
            session.close()

    def get_daily_learning_materials(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recommended daily learning materials

        Args:
            category: Filter by category
            limit: Number of materials

        Returns:
            List of learning materials
        """
        session = self.db_manager.get_session()

        try:
            query = session.query(NewsArticleDB).order_by(
                NewsArticleDB.scraped_at.desc()
            )

            if category:
                query = query.filter_by(category=category)

            articles = query.limit(limit).all()

            materials = []
            for article in articles:
                materials.append({
                    'id': article.id,
                    'title': article.title,
                    'source': article.source,
                    'category': article.category,
                    'summary': article.summary,
                    'sentiment': article.sentiment,
                    'keywords': article.keywords,
                    'url': article.url
                })

            return materials

        except Exception as e:
            logger.error(f"Error getting daily materials: {str(e)}")
            return []

        finally:
            session.close()


# Service instance
_learning_service: Optional[LearningService] = None


def get_learning_service() -> LearningService:
    """Get or create learning service instance"""
    global _learning_service
    if _learning_service is None:
        _learning_service = LearningService()
    return _learning_service


# Example usage
if __name__ == "__main__":
    # Test learning service
    service = LearningService()

    # Create sample news article
    sample_article = NewsArticle(
        title="AI 기술 발전으로 교육 분야 혁신",
        source="Tech News",
        url="https://example.com/ai-education",
        category="IT"
    )

    # Generate summary
    summary = service.generate_summary(sample_article)
    print(f"Summary:\n{summary}\n")

    # Generate quiz
    quiz = service.generate_quiz(sample_article, num_questions=3)
    print(f"Quiz questions: {len(quiz)}")

    # Generate flashcards
    flashcards = service.generate_flashcards(sample_article, num_cards=5)
    print(f"Flashcards: {len(flashcards)}")
