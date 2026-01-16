"""
AI Tutor Service - Interactive chatbot for student learning
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import anthropic
import uuid

from src.config import settings
from src.logger import setup_logger
from src.models.database import (
    get_db_manager,
    ChatMessage,
    LearningMaterial,
    NewsArticleDB,
    User
)

logger = setup_logger("daip.ai_tutor")


class AITutor:
    """AI-powered tutor for student questions"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI tutor"""
        self.api_key = api_key or settings.anthropic_api_key
        if self.api_key:
            self.client = anthropic.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("Anthropic API key not configured")

        self.db_manager = get_db_manager()
        self.system_prompt = """당신은 대학생을 위한 친절하고 전문적인 AI 튜터입니다.

역할:
1. 학습 내용에 대한 질문에 답변
2. 개념을 쉽게 설명
3. 추가 학습 자료 제안
4. 학습 동기 부여

답변 스타일:
- 친근하고 격려하는 어조
- 단계별로 설명
- 예시와 비유 활용
- 추가 질문 유도

제한사항:
- 숙제를 대신 해주지 않음
- 부정행위 도움 거부
- 학습 과정을 중시"""

        logger.info("AI Tutor initialized")

    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get chat history for context"""
        session = self.db_manager.get_session()

        try:
            messages = session.query(ChatMessage).filter_by(
                session_id=session_id
            ).order_by(
                ChatMessage.created_at.desc()
            ).limit(limit).all()

            # Reverse to chronological order
            messages = list(reversed(messages))

            return [
                {"role": msg.role, "content": msg.content}
                for msg in messages
                if msg.role in ["user", "assistant"]
            ]

        finally:
            session.close()

    def get_relevant_context(
        self,
        user_id: int,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """Get relevant learning materials for context"""
        session = self.db_manager.get_session()

        try:
            # Get recent learning materials
            materials = session.query(LearningMaterial).filter_by(
                user_id=user_id
            ).order_by(
                LearningMaterial.created_at.desc()
            ).limit(3).all()

            if not materials:
                return None

            context = {
                "recent_materials": [
                    {
                        "title": m.title,
                        "type": m.material_type,
                        "category": m.news_article.category if m.news_article else None
                    }
                    for m in materials
                ]
            }

            return context

        finally:
            session.close()

    def chat(
        self,
        user_id: int,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat with AI tutor

        Args:
            user_id: User ID
            message: User's message
            session_id: Chat session ID (create new if None)

        Returns:
            Response with answer and session_id
        """
        if not self.client:
            return {
                "answer": "AI 튜터 서비스를 사용할 수 없습니다.",
                "session_id": session_id
            }

        # Create or use existing session
        if not session_id:
            session_id = str(uuid.uuid4())

        session = self.db_manager.get_session()

        try:
            # Save user message
            user_message = ChatMessage(
                user_id=user_id,
                session_id=session_id,
                role="user",
                content=message
            )
            session.add(user_message)
            session.commit()

            # Get chat history
            chat_history = self.get_chat_history(session_id)

            # Get relevant context
            context = self.get_relevant_context(user_id, message)

            # Build context message
            context_msg = ""
            if context and context.get("recent_materials"):
                context_msg = "\n\n최근 학습 자료:\n"
                for mat in context["recent_materials"]:
                    context_msg += f"- {mat['title']} ({mat['type']})\n"

            # Create messages for Claude
            messages = []

            # Add chat history
            for msg in chat_history:
                messages.append(msg)

            # Add current message (if not already in history)
            if not messages or messages[-1]["content"] != message:
                messages.append({"role": "user", "content": message + context_msg})

            # Get AI response
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=self.system_prompt,
                messages=messages
            )

            answer = response.content[0].text

            # Save AI response
            ai_message = ChatMessage(
                user_id=user_id,
                session_id=session_id,
                role="assistant",
                content=answer,
                context=context
            )
            session.add(ai_message)
            session.commit()

            logger.info(f"AI Tutor responded to user {user_id}")

            return {
                "answer": answer,
                "session_id": session_id,
                "context": context
            }

        except Exception as e:
            logger.error(f"Error in AI tutor chat: {str(e)}")
            session.rollback()
            return {
                "answer": "죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.",
                "session_id": session_id
            }

        finally:
            session.close()

    def explain_concept(
        self,
        concept: str,
        level: str = "intermediate"
    ) -> str:
        """
        Explain a concept at different levels

        Args:
            concept: Concept to explain
            level: beginner, intermediate, advanced

        Returns:
            Explanation
        """
        if not self.client:
            return "AI 서비스를 사용할 수 없습니다."

        try:
            level_descriptions = {
                "beginner": "고등학생도 이해할 수 있게",
                "intermediate": "대학생 수준으로",
                "advanced": "전문적이고 심화된 내용으로"
            }

            prompt = f"""{concept}에 대해 {level_descriptions.get(level, '대학생 수준으로')} 설명해주세요.

요구사항:
1. 핵심 개념 정의
2. 쉬운 예시
3. 실생활 적용 사례
4. 관련 개념 연결
5. 추가 학습 자료 제안

설명을 작성해주세요:"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error explaining concept: {str(e)}")
            return "개념 설명 중 오류가 발생했습니다."

    def get_study_tips(
        self,
        category: str,
        user_stats: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Get personalized study tips

        Args:
            category: Subject category
            user_stats: User's learning statistics

        Returns:
            List of study tips
        """
        if not self.client:
            return ["AI 서비스를 사용할 수 없습니다."]

        try:
            stats_context = ""
            if user_stats:
                stats_context = f"""
사용자 통계:
- 퀴즈 정답률: {user_stats.get('quiz_accuracy', 0)}%
- 학습 자료 완료율: {user_stats.get('completion_rate', 0)}%
- 연속 학습일: {user_stats.get('streak', 0)}일
"""

            prompt = f"""{category} 분야 학습을 위한 맞춤형 학습 팁 5개를 제공해주세요.

{stats_context}

각 팁은 구체적이고 실행 가능해야 합니다.
JSON 배열 형식으로 응답:
["팁1", "팁2", "팁3", "팁4", "팁5"]"""

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            import re

            content = response.content[0].text
            json_match = re.search(r'\[.*\]', content, re.DOTALL)

            if json_match:
                tips = json.loads(json_match.group(0))
                return tips

            return [content]

        except Exception as e:
            logger.error(f"Error getting study tips: {str(e)}")
            return ["학습 팁을 가져오는 중 오류가 발생했습니다."]

    def get_chat_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's chat sessions"""
        session = self.db_manager.get_session()

        try:
            # Get unique sessions with latest message
            from sqlalchemy import func

            sessions = session.query(
                ChatMessage.session_id,
                func.max(ChatMessage.created_at).label('last_message'),
                func.count(ChatMessage.id).label('message_count')
            ).filter_by(
                user_id=user_id
            ).group_by(
                ChatMessage.session_id
            ).order_by(
                func.max(ChatMessage.created_at).desc()
            ).all()

            return [
                {
                    "session_id": s.session_id,
                    "last_message": s.last_message,
                    "message_count": s.message_count
                }
                for s in sessions
            ]

        finally:
            session.close()


# Service instance
_ai_tutor: Optional[AITutor] = None


def get_ai_tutor() -> AITutor:
    """Get or create AI tutor instance"""
    global _ai_tutor
    if _ai_tutor is None:
        _ai_tutor = AITutor()
    return _ai_tutor


# Example usage
if __name__ == "__main__":
    # Test AI tutor
    tutor = AITutor()

    # Test chat
    response = tutor.chat(
        user_id=1,
        message="AI와 머신러닝의 차이가 뭔가요?"
    )

    print(f"Answer: {response['answer']}")
    print(f"Session ID: {response['session_id']}")

    # Test concept explanation
    explanation = tutor.explain_concept("딥러닝", level="intermediate")
    print(f"\nExplanation:\n{explanation}")

    # Test study tips
    tips = tutor.get_study_tips("AI", {"quiz_accuracy": 75, "streak": 5})
    print(f"\nStudy Tips:")
    for i, tip in enumerate(tips, 1):
        print(f"{i}. {tip}")
