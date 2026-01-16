"""
AI Tutor Chat API router
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from typing import List, Optional
from pydantic import BaseModel

from src.services.ai_tutor import get_ai_tutor
from src.api.websocket import get_connection_manager
from src.logger import setup_logger

logger = setup_logger("daip.api.chat")

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    context: Optional[dict] = None


class ExplainConceptRequest(BaseModel):
    concept: str
    level: str = "intermediate"


@router.post("/ask", response_model=ChatResponse)
async def ask_ai_tutor(
    request: ChatRequest,
    user_id: int = 1  # TODO: Get from authentication
):
    """Ask AI tutor a question"""
    try:
        tutor = get_ai_tutor()
        response = tutor.chat(
            user_id=user_id,
            message=request.message,
            session_id=request.session_id
        )

        return ChatResponse(
            answer=response["answer"],
            session_id=response["session_id"],
            context=response.get("context")
        )

    except Exception as e:
        logger.error(f"Error in AI tutor chat: {str(e)}")
        return ChatResponse(
            answer="죄송합니다. 일시적인 오류가 발생했습니다.",
            session_id=request.session_id or "error",
            context=None
        )


@router.post("/explain")
async def explain_concept(request: ExplainConceptRequest):
    """Get explanation of a concept"""
    tutor = get_ai_tutor()
    explanation = tutor.explain_concept(
        concept=request.concept,
        level=request.level
    )

    return {
        "concept": request.concept,
        "level": request.level,
        "explanation": explanation
    }


@router.get("/sessions")
async def get_chat_sessions(
    user_id: int = 1  # TODO: Get from authentication
):
    """Get user's chat sessions"""
    tutor = get_ai_tutor()
    sessions = tutor.get_chat_sessions(user_id)

    return {
        "user_id": user_id,
        "total_sessions": len(sessions),
        "sessions": sessions
    }


@router.get("/tips/{category}")
async def get_study_tips(
    category: str,
    user_id: int = 1  # TODO: Get from authentication
):
    """Get personalized study tips"""
    tutor = get_ai_tutor()

    # TODO: Get actual user stats
    user_stats = {
        "quiz_accuracy": 75,
        "completion_rate": 60,
        "streak": 5
    }

    tips = tutor.get_study_tips(category, user_stats)

    return {
        "category": category,
        "tips": tips
    }


@router.websocket("/ws/{user_id}")
async def websocket_chat(
    websocket: WebSocket,
    user_id: int
):
    """WebSocket endpoint for real-time chat"""
    manager = get_connection_manager()
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message = data.get("message", "")
            session_id = data.get("session_id")

            # Get AI response
            tutor = get_ai_tutor()
            response = tutor.chat(
                user_id=user_id,
                message=message,
                session_id=session_id
            )

            # Send response back
            await websocket.send_json({
                "type": "chat_response",
                "answer": response["answer"],
                "session_id": response["session_id"],
                "context": response.get("context")
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected from chat")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket, user_id)
