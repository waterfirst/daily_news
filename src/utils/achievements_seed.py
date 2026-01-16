"""
Seed achievements data for gamification
"""
from src.models.database import get_db_manager, Achievement
from src.logger import setup_logger

logger = setup_logger("daip.achievements_seed")


ACHIEVEMENTS = [
    # Quiz achievements
    {
        "name": "퀴즈 초보자",
        "description": "첫 퀴즈 완료",
        "icon": "🎯",
        "category": "quiz",
        "requirement": {"quiz_count": 1},
        "points": 10
    },
    {
        "name": "퀴즈 마스터",
        "description": "퀴즈 100개 완료",
        "icon": "🏆",
        "category": "quiz",
        "requirement": {"quiz_count": 100},
        "points": 100
    },
    {
        "name": "완벽주의자",
        "description": "퀴즈 10개 연속 정답",
        "icon": "💯",
        "category": "quiz",
        "requirement": {"consecutive_correct": 10},
        "points": 50
    },
    {
        "name": "정확도 킹",
        "description": "정답률 90% 이상 달성",
        "icon": "🎓",
        "category": "quiz",
        "requirement": {"accuracy": 90},
        "points": 75
    },

    # Streak achievements
    {
        "name": "시작이 반",
        "description": "3일 연속 학습",
        "icon": "🔥",
        "category": "streak",
        "requirement": {"streak_days": 3},
        "points": 15
    },
    {
        "name": "일주일의 기적",
        "description": "7일 연속 학습",
        "icon": "⭐",
        "category": "streak",
        "requirement": {"streak_days": 7},
        "points": 30
    },
    {
        "name": "한 달의 열정",
        "description": "30일 연속 학습",
        "icon": "🌟",
        "category": "streak",
        "requirement": {"streak_days": 30},
        "points": 100
    },
    {
        "name": "백일의 성실",
        "description": "100일 연속 학습",
        "icon": "💎",
        "category": "streak",
        "requirement": {"streak_days": 100},
        "points": 500
    },

    # Learning achievements
    {
        "name": "학습 탐험가",
        "description": "10개 학습 자료 완료",
        "icon": "📚",
        "category": "learning",
        "requirement": {"materials_completed": 10},
        "points": 20
    },
    {
        "name": "지식 수집가",
        "description": "50개 학습 자료 완료",
        "icon": "📖",
        "category": "learning",
        "requirement": {"materials_completed": 50},
        "points": 75
    },
    {
        "name": "다재다능",
        "description": "5개 이상 카테고리 학습",
        "icon": "🌈",
        "category": "learning",
        "requirement": {"categories_count": 5},
        "points": 50
    },

    # Social achievements
    {
        "name": "친구 만들기",
        "description": "첫 스터디 그룹 가입",
        "icon": "👥",
        "category": "social",
        "requirement": {"group_joined": 1},
        "points": 10
    },
    {
        "name": "그룹 리더",
        "description": "스터디 그룹 생성",
        "icon": "👑",
        "category": "social",
        "requirement": {"group_created": 1},
        "points": 25
    },
    {
        "name": "소셜 마스터",
        "description": "그룹 활동 50회 참여",
        "icon": "💬",
        "category": "social",
        "requirement": {"group_activities": 50},
        "points": 60
    },
    {
        "name": "인기 스타",
        "description": "3개 이상 그룹에서 활동",
        "icon": "⭐",
        "category": "social",
        "requirement": {"active_groups": 3},
        "points": 40
    },

    # Special achievements
    {
        "name": "얼리버드",
        "description": "아침 6시 이전 학습",
        "icon": "🌅",
        "category": "special",
        "requirement": {"early_study": True},
        "points": 20
    },
    {
        "name": "올빼미",
        "description": "자정 이후 학습",
        "icon": "🦉",
        "category": "special",
        "requirement": {"late_study": True},
        "points": 20
    },
    {
        "name": "주말 전사",
        "description": "주말에도 학습",
        "icon": "💪",
        "category": "special",
        "requirement": {"weekend_study": 10},
        "points": 30
    },
    {
        "name": "AI 친구",
        "description": "AI 튜터와 10회 대화",
        "icon": "🤖",
        "category": "special",
        "requirement": {"ai_chats": 10},
        "points": 25
    },
]


def seed_achievements():
    """Seed achievements into database"""
    db_manager = get_db_manager()
    session = db_manager.get_session()

    try:
        # Check if achievements already exist
        existing_count = session.query(Achievement).count()

        if existing_count > 0:
            logger.info(f"Achievements already seeded ({existing_count} found)")
            return

        # Insert achievements
        for ach_data in ACHIEVEMENTS:
            achievement = Achievement(**ach_data)
            session.add(achievement)

        session.commit()
        logger.info(f"Successfully seeded {len(ACHIEVEMENTS)} achievements")

    except Exception as e:
        logger.error(f"Error seeding achievements: {str(e)}")
        session.rollback()

    finally:
        session.close()


if __name__ == "__main__":
    seed_achievements()
