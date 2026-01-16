"""
WebSocket manager for real-time notifications
"""
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime

from src.logger import setup_logger

logger = setup_logger("daip.websocket")


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Room-based connections (for study groups)
        self.room_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a user"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user"""
        if user_id in self.active_connections:
            message_json = json.dumps(message)

            # Send to all connections of this user
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all users"""
        message_json = json.dumps(message)

        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {str(e)}")

    async def join_room(self, websocket: WebSocket, room_id: str):
        """Join a room (study group)"""
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()

        self.room_connections[room_id].add(websocket)
        logger.info(f"WebSocket joined room {room_id}")

    async def leave_room(self, websocket: WebSocket, room_id: str):
        """Leave a room"""
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(websocket)

            if not self.room_connections[room_id]:
                del self.room_connections[room_id]

        logger.info(f"WebSocket left room {room_id}")

    async def send_to_room(self, message: dict, room_id: str):
        """Send message to all members of a room"""
        if room_id not in self.room_connections:
            return

        message_json = json.dumps(message)

        for connection in self.room_connections[room_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to room {room_id}: {str(e)}")


# Singleton instance
_manager: ConnectionManager = None


def get_connection_manager() -> ConnectionManager:
    """Get or create connection manager"""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


class NotificationService:
    """Service for sending notifications via WebSocket"""

    def __init__(self):
        self.manager = get_connection_manager()

    async def notify_quiz_result(self, user_id: int, quiz_data: dict):
        """Notify user of quiz result"""
        await self.manager.send_personal_message({
            "type": "quiz_result",
            "timestamp": datetime.now().isoformat(),
            "data": quiz_data
        }, user_id)

    async def notify_new_material(self, user_id: int, material_data: dict):
        """Notify user of new learning material"""
        await self.manager.send_personal_message({
            "type": "new_material",
            "timestamp": datetime.now().isoformat(),
            "data": material_data
        }, user_id)

    async def notify_streak_achieved(self, user_id: int, streak_days: int):
        """Notify user of study streak achievement"""
        await self.manager.send_personal_message({
            "type": "streak_achievement",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "streak_days": streak_days,
                "message": f"🔥 {streak_days}일 연속 학습! 대단해요!"
            }
        }, user_id)

    async def notify_new_news(self, category: str, count: int):
        """Broadcast new news availability"""
        await self.manager.broadcast({
            "type": "new_news",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "category": category,
                "count": count,
                "message": f"{category} 카테고리에 새로운 뉴스 {count}개가 추가되었습니다."
            }
        })

    async def notify_group_activity(self, room_id: str, activity_data: dict):
        """Notify study group of activity"""
        await self.manager.send_to_room({
            "type": "group_activity",
            "timestamp": datetime.now().isoformat(),
            "data": activity_data
        }, room_id)

    async def notify_leaderboard_update(self, leaderboard_data: dict):
        """Broadcast leaderboard update"""
        await self.manager.broadcast({
            "type": "leaderboard_update",
            "timestamp": datetime.now().isoformat(),
            "data": leaderboard_data
        })


# Singleton instance
_notification_service: NotificationService = None


def get_notification_service() -> NotificationService:
    """Get or create notification service"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
