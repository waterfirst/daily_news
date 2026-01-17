"""
Configuration management for Daily Automated Intelligence Platform (DAIP)
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Telegram Configuration
    telegram_bot_token: str = Field(
        default="",
        description="Telegram bot token from BotFather"
    )
    telegram_chat_id: str = Field(
        default="",
        description="Telegram chat ID for notifications"
    )

    # API Keys
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic Claude API key"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )

    # Financial Data APIs
    stock_api_key: Optional[str] = Field(
        default=None,
        description="Stock market data API key"
    )
    yahoo_finance_api_key: Optional[str] = Field(
        default=None,
        description="Yahoo Finance API key"
    )

    # News APIs
    news_api_key: Optional[str] = Field(
        default=None,
        description="News API key"
    )
    naver_client_id: Optional[str] = Field(
        default=None,
        description="Naver API client ID"
    )
    naver_client_secret: Optional[str] = Field(
        default=None,
        description="Naver API client secret"
    )

    # Database Configuration
    database_url: str = Field(
        default=f"sqlite:///{BASE_DIR}/data/database.db",
        description="Database connection URL"
    )
    database_backup_enabled: bool = Field(
        default=True,
        description="Enable database backups"
    )

    # Scheduler Configuration
    timezone: str = Field(
        default="Asia/Seoul",
        description="Timezone for scheduler"
    )
    enable_scheduler: bool = Field(
        default=True,
        description="Enable job scheduler"
    )

    # Service Configuration
    etf_service_enabled: bool = Field(
        default=True,
        description="Enable ETF analysis service"
    )
    news_service_enabled: bool = Field(
        default=True,
        description="Enable news scraping service"
    )
    content_service_enabled: bool = Field(
        default=True,
        description="Enable AI content generation service"
    )
    beauty_news_enabled: bool = Field(
        default=True,
        description="Enable beauty news service"
    )
    display_news_enabled: bool = Field(
        default=True,
        description="Enable display news service"
    )
    semiconductor_news_enabled: bool = Field(
        default=True,
        description="Enable semiconductor news service"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: str = Field(
        default="logs/daip.log",
        description="Log file path"
    )

    # Cache Configuration
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching"
    )
    cache_ttl: int = Field(
        default=3600,
        description="Cache time-to-live in seconds"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    max_requests_per_minute: int = Field(
        default=30,
        description="Maximum requests per minute"
    )

    # Debug Mode
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    @property
    def data_dir(self) -> Path:
        """Data directory path"""
        return BASE_DIR / "data"

    @property
    def cache_dir(self) -> Path:
        """Cache directory path"""
        return self.data_dir / "cache"

    @property
    def logs_dir(self) -> Path:
        """Logs directory path"""
        return BASE_DIR / "logs"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.ensure_directories()


# Service-specific configurations
class ETFConfig:
    """ETF analysis service configuration"""
    SCHEDULE_TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
    LOOKBACK_DAYS = 30
    STOCHASTIC_PERIOD = 14
    OVERSOLD_THRESHOLD = 20
    OVERBOUGHT_THRESHOLD = 80
    TOP_N_RECOMMENDATIONS = 5

    # Korean ETF tickers
    ETF_TICKERS = [
        "069500.KS",  # KODEX 200
        "102110.KS",  # TIGER 200
        "251350.KS",  # KODEX 코스닥150
        "091160.KS",  # KODEX 반도체
        "091180.KS",  # KODEX 은행
    ]


class NewsConfig:
    """News scraping service configuration"""
    SCHEDULE_TIMES = ["10:00", "12:00", "14:00"]
    CATEGORIES = ["정치", "경제", "사회", "IT", "AI"]
    TOP_N_NEWS = 5
    DUPLICATE_THRESHOLD = 0.8

    # News sources
    SOURCES = {
        "naver": "https://news.naver.com",
        "google": "https://news.google.com",
        "medium": "https://medium.com/tag/ai",
    }


class ContentConfig:
    """Content generation service configuration"""
    SCHEDULE_TIME = "23:00"
    CONTENT_TYPES = ["column", "travel", "tech_analysis"]
    OUTPUT_FORMATS = ["blog", "newsletter", "pdf"]
    OUTPUT_DIR = str(BASE_DIR / "data" / "content")
    MIN_WORDS = 500
    MAX_WORDS = 2000


class BeautyNewsConfig:
    """Beauty news service configuration"""
    SCHEDULE_TIMES = ["11:00", "15:00"]
    SOURCES = {
        "cosme": "https://www.cosme.net",
        "japanese_pr": "https://prtimes.jp/main/html/searchrlp/company_id/",
    }
    CATEGORIES = ["신기술", "마켓 트렌드", "회사 뉴스", "특허"]


class DisplayNewsConfig:
    """Display news service configuration"""
    SCHEDULE_TIMES = ["10:00", "14:00"]
    COUNTRIES = ["한국", "중국", "일본", "대만"]
    KEYWORDS = ["OLED", "Micro LED", "QD-dot", "LCD"]


class SemiconductorNewsConfig:
    """Semiconductor/Robot/Bio news service configuration"""
    SCHEDULE_TIMES = ["09:00", "13:00"]
    CATEGORIES = ["반도체", "로봇", "바이오"]
    SOURCES_US = [
        "https://www.wsj.com/tech",
        "https://www.cnbc.com/technology",
        "https://www.reuters.com/technology",
    ]
    SOURCES_KR = [
        "https://www.mk.co.kr/news/it",
        "https://www.hankyung.com/it",
        "https://www.etnews.com",
    ]
