"""
Social features API router - Study groups and collaborative learning
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from src.models.database import (
    StudyGroup, StudyGroupMember, GroupActivity,
    Achievement, UserAchievement,
    get_db, User
)
from src.logger import setup_logger
from src.api.websocket import get_notification_service

logger = setup_logger("daip.api.social")

router = APIRouter()


# Pydantic models
class CreateStudyGroup(BaseModel):
    name: str
    description: str
    category: str
    max_members: int = 10
    is_public: bool = True


class StudyGroupResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    member_count: int
    max_members: int
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


class JoinGroupRequest(BaseModel):
    group_id: int


class GroupActivityResponse(BaseModel):
    id: int
    user_id: int
    activity_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/groups", response_model=StudyGroupResponse)
async def create_study_group(
    group_data: CreateStudyGroup,
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Create a new study group"""
    try:
        # Create group
        group = StudyGroup(
            name=group_data.name,
            description=group_data.description,
            category=group_data.category,
            max_members=group_data.max_members,
            is_public=group_data.is_public,
            created_by=user_id
        )

        db.add(group)
        db.commit()
        db.refresh(group)

        # Add creator as admin
        member = StudyGroupMember(
            group_id=group.id,
            user_id=user_id,
            role="admin"
        )

        db.add(member)
        db.commit()

        logger.info(f"Study group created: {group.name} by user {user_id}")

        return StudyGroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            category=group.category,
            member_count=1,
            max_members=group.max_members,
            is_public=group.is_public,
            created_at=group.created_at
        )

    except Exception as e:
        logger.error(f"Error creating study group: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create study group")


@router.get("/groups", response_model=List[StudyGroupResponse])
async def list_study_groups(
    category: Optional[str] = None,
    is_public: bool = True,
    db: Session = Depends(get_db)
):
    """List available study groups"""
    query = db.query(StudyGroup).filter_by(is_public=is_public)

    if category:
        query = query.filter_by(category=category)

    groups = query.all()

    # Add member count
    results = []
    for group in groups:
        member_count = db.query(StudyGroupMember).filter_by(
            group_id=group.id,
            is_active=True
        ).count()

        results.append(StudyGroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            category=group.category,
            member_count=member_count,
            max_members=group.max_members,
            is_public=group.is_public,
            created_at=group.created_at
        ))

    return results


@router.post("/groups/join")
async def join_study_group(
    request: JoinGroupRequest,
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Join a study group"""
    # Check if group exists
    group = db.query(StudyGroup).filter_by(id=request.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if already a member
    existing = db.query(StudyGroupMember).filter_by(
        group_id=request.group_id,
        user_id=user_id,
        is_active=True
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already a member")

    # Check member limit
    current_members = db.query(StudyGroupMember).filter_by(
        group_id=request.group_id,
        is_active=True
    ).count()

    if current_members >= group.max_members:
        raise HTTPException(status_code=400, detail="Group is full")

    # Add member
    member = StudyGroupMember(
        group_id=request.group_id,
        user_id=user_id,
        role="member"
    )

    db.add(member)

    # Log activity
    activity = GroupActivity(
        group_id=request.group_id,
        user_id=user_id,
        activity_type="member_joined",
        content=f"New member joined the group"
    )

    db.add(activity)
    db.commit()

    # Send notification
    notification_service = get_notification_service()
    await notification_service.notify_group_activity(
        room_id=f"group_{request.group_id}",
        activity_data={
            "type": "member_joined",
            "user_id": user_id,
            "group_id": request.group_id
        }
    )

    return {"message": "Successfully joined group", "group_id": request.group_id}


@router.get("/groups/{group_id}/activities", response_model=List[GroupActivityResponse])
async def get_group_activities(
    group_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get group activity feed"""
    activities = db.query(GroupActivity).filter_by(
        group_id=group_id
    ).order_by(
        GroupActivity.created_at.desc()
    ).limit(limit).all()

    return activities


@router.post("/groups/{group_id}/activity")
async def post_group_activity(
    group_id: int,
    activity_type: str,
    content: str,
    user_id: int = 1,  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """Post activity to group feed"""
    # Verify membership
    member = db.query(StudyGroupMember).filter_by(
        group_id=group_id,
        user_id=user_id,
        is_active=True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a group member")

    # Create activity
    activity = GroupActivity(
        group_id=group_id,
        user_id=user_id,
        activity_type=activity_type,
        content=content
    )

    db.add(activity)
    db.commit()

    # Award points
    member.points += 5
    db.commit()

    # Send notification
    notification_service = get_notification_service()
    await notification_service.notify_group_activity(
        room_id=f"group_{group_id}",
        activity_data={
            "type": activity_type,
            "user_id": user_id,
            "content": content
        }
    )

    return {"message": "Activity posted", "points_earned": 5}


@router.get("/leaderboard")
async def get_leaderboard(
    group_id: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get leaderboard (global or group-specific)"""
    if group_id:
        # Group leaderboard
        members = db.query(
            StudyGroupMember,
            User
        ).join(
            User,
            User.id == StudyGroupMember.user_id
        ).filter(
            StudyGroupMember.group_id == group_id,
            StudyGroupMember.is_active == True
        ).order_by(
            StudyGroupMember.points.desc()
        ).limit(limit).all()

        return {
            "type": "group",
            "group_id": group_id,
            "leaderboard": [
                {
                    "rank": idx + 1,
                    "user_id": member.user_id,
                    "username": user.username,
                    "points": member.points
                }
                for idx, (member, user) in enumerate(members)
            ]
        }
    else:
        # Global leaderboard (by quiz results)
        from sqlalchemy import func
        from src.models.database import QuizResult

        top_users = db.query(
            QuizResult.user_id,
            User.username,
            func.count(QuizResult.id).label('total_quizzes'),
            func.sum(func.cast(QuizResult.is_correct, db.Integer)).label('correct_answers')
        ).join(
            User,
            User.id == QuizResult.user_id
        ).group_by(
            QuizResult.user_id,
            User.username
        ).order_by(
            func.sum(func.cast(QuizResult.is_correct, db.Integer)).desc()
        ).limit(limit).all()

        return {
            "type": "global",
            "leaderboard": [
                {
                    "rank": idx + 1,
                    "user_id": user.user_id,
                    "username": user.username,
                    "total_quizzes": user.total_quizzes,
                    "correct_answers": user.correct_answers or 0,
                    "accuracy": round((user.correct_answers or 0) / user.total_quizzes * 100, 2) if user.total_quizzes > 0 else 0
                }
                for idx, user in enumerate(top_users)
            ]
        }


@router.get("/achievements")
async def list_achievements(db: Session = Depends(get_db)):
    """List all available achievements"""
    achievements = db.query(Achievement).all()

    return {
        "total": len(achievements),
        "achievements": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "category": a.category,
                "points": a.points
            }
            for a in achievements
        ]
    }


@router.get("/achievements/user/{user_id}")
async def get_user_achievements(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's earned achievements"""
    user_achievements = db.query(
        UserAchievement,
        Achievement
    ).join(
        Achievement,
        Achievement.id == UserAchievement.achievement_id
    ).filter(
        UserAchievement.user_id == user_id
    ).all()

    return {
        "user_id": user_id,
        "total_achievements": len(user_achievements),
        "total_points": sum(a.points for _, a in user_achievements),
        "achievements": [
            {
                "id": achievement.id,
                "name": achievement.name,
                "earned_at": user_achievement.earned_at,
                "points": achievement.points
            }
            for user_achievement, achievement in user_achievements
        ]
    }
