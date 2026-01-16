"""
WebSocket notifications API router
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from src.api.websocket import get_connection_manager, get_notification_service
from src.logger import setup_logger

logger = setup_logger("daip.api.notifications")

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int = Query(...)
):
    """
    WebSocket endpoint for real-time notifications

    Connect to: ws://localhost:8000/api/notifications/ws?user_id=1

    Message types:
    - quiz_result: Quiz completion notification
    - new_material: New learning material available
    - streak_achievement: Study streak milestone
    - new_news: New news articles available
    - group_activity: Study group activity
    - leaderboard_update: Leaderboard changed
    """
    manager = get_connection_manager()
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()

            # Echo back for testing
            await websocket.send_json({
                "type": "echo",
                "message": f"Received: {data}",
                "user_id": user_id
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected from notifications")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        manager.disconnect(websocket, user_id)


@router.websocket("/ws/group/{group_id}")
async def websocket_group(
    websocket: WebSocket,
    group_id: int,
    user_id: int = Query(...)
):
    """
    WebSocket endpoint for study group real-time updates

    Connect to: ws://localhost:8000/api/notifications/ws/group/1?user_id=1
    """
    manager = get_connection_manager()

    # Connect user and join room
    await manager.connect(websocket, user_id)
    await manager.join_room(websocket, f"group_{group_id}")

    try:
        while True:
            # Listen for messages from group members
            data = await websocket.receive_json()

            message_type = data.get("type", "message")
            content = data.get("content", "")

            # Broadcast to all group members
            await manager.send_to_room(
                {
                    "type": message_type,
                    "user_id": user_id,
                    "content": content,
                    "group_id": group_id
                },
                f"group_{group_id}"
            )

    except WebSocketDisconnect:
        await manager.leave_room(websocket, f"group_{group_id}")
        manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} left group {group_id}")
    except Exception as e:
        logger.error(f"Group WebSocket error: {str(e)}")
        await manager.leave_room(websocket, f"group_{group_id}")
        manager.disconnect(websocket, user_id)


@router.get("/test/send")
async def test_notification(
    user_id: int,
    notification_type: str = "quiz_result"
):
    """Test endpoint to send notifications"""
    notification_service = get_notification_service()

    if notification_type == "quiz_result":
        await notification_service.notify_quiz_result(
            user_id=user_id,
            quiz_data={
                "quiz_id": 1,
                "is_correct": True,
                "score": 80
            }
        )
    elif notification_type == "streak":
        await notification_service.notify_streak_achieved(
            user_id=user_id,
            streak_days=7
        )
    elif notification_type == "new_news":
        await notification_service.notify_new_news(
            category="IT",
            count=5
        )

    return {
        "message": "Test notification sent",
        "type": notification_type,
        "user_id": user_id
    }
