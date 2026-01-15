"""
Telegram Bot for Daily Automated Intelligence Platform (DAIP)
Sends notifications and reports via Telegram
"""
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from src.config import settings
from src.logger import setup_logger

logger = setup_logger("daip.telegram")


class TelegramBot:
    """Telegram bot for sending notifications and reports"""

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram bot

        Args:
            token: Telegram bot token (from BotFather)
            chat_id: Default chat ID for sending messages
        """
        self.token = token or settings.telegram_bot_token
        self.chat_id = chat_id or settings.telegram_chat_id

        if not self.token:
            logger.error("Telegram bot token not configured")
            raise ValueError("TELEGRAM_BOT_TOKEN must be set in environment variables")

        if not self.chat_id:
            logger.warning("Telegram chat ID not configured, messages won't be sent by default")

        self.bot = telebot.TeleBot(self.token)
        logger.info("Telegram bot initialized successfully")

    def send_message(
        self,
        message: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
        disable_notification: bool = False
    ) -> bool:
        """
        Send a text message via Telegram

        Args:
            message: Message text
            chat_id: Target chat ID (uses default if not provided)
            parse_mode: Parse mode (HTML, Markdown, or None)
            disable_notification: Send silently

        Returns:
            True if successful, False otherwise
        """
        target_chat_id = chat_id or self.chat_id
        if not target_chat_id:
            logger.error("No chat ID provided")
            return False

        try:
            self.bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_notification=disable_notification
            )
            logger.info(f"Message sent successfully to {target_chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False

    def send_etf_report(self, etf_data: List[Dict[str, Any]], timestamp: Optional[datetime] = None) -> bool:
        """
        Send ETF analysis report

        Args:
            etf_data: List of ETF recommendations
            timestamp: Report timestamp

        Returns:
            True if successful, False otherwise
        """
        if not etf_data:
            logger.warning("No ETF data to send")
            return False

        timestamp = timestamp or datetime.now()
        time_str = timestamp.strftime("%H:%M")

        # Format message
        message = f"📈 <b>{time_str} ETF 추천 리포트</b>\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for idx, etf in enumerate(etf_data[:5], 1):
            ticker = etf.get('ticker', 'N/A')
            name = etf.get('name', ticker)
            change = etf.get('change_pct', 0)
            stoch = etf.get('stochastic', 0)
            signal = etf.get('signal', 'HOLD')

            emoji = "🟢" if signal == "BUY" else "🟡" if signal == "WATCH" else "⚪"

            message += f"{emoji} <b>{idx}. {name}</b>\n"
            message += f"   변화율: {change:+.2f}% | Stoch: {stoch:.1f}\n"
            message += f"   신호: {signal}\n\n"

        message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"💡 보고시각: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_message(message)

    def send_news_report(self, news_items: List[Dict[str, Any]], category: str = "종합") -> bool:
        """
        Send news scraping report

        Args:
            news_items: List of news articles
            category: News category

        Returns:
            True if successful, False otherwise
        """
        if not news_items:
            logger.warning("No news items to send")
            return False

        timestamp = datetime.now()
        time_str = timestamp.strftime("%H:%M")

        # Format message
        message = f"📰 <b>{time_str} {category} 뉴스</b>\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for idx, news in enumerate(news_items[:5], 1):
            title = news.get('title', 'No title')
            source = news.get('source', 'Unknown')
            url = news.get('url', '#')
            sentiment = news.get('sentiment', 'neutral')

            sentiment_emoji = "😊" if sentiment == "positive" else "😟" if sentiment == "negative" else "😐"

            message += f"{sentiment_emoji} <b>{idx}. {title}</b>\n"
            message += f"   출처: {source}\n"
            message += f"   <a href='{url}'>기사 보기</a>\n\n"

        message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"🕐 수집시각: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_message(message)

    def send_error_notification(self, service_name: str, error_message: str) -> bool:
        """
        Send error notification

        Args:
            service_name: Name of the service that failed
            error_message: Error details

        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"⚠️ <b>시스템 오류 발생</b>\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += f"<b>서비스:</b> {service_name}\n"
        message += f"<b>발생시각:</b> {timestamp}\n"
        message += f"<b>오류내용:</b>\n<code>{error_message}</code>\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━"

        return self.send_message(message)

    def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """
        Send daily summary report

        Args:
            summary_data: Summary statistics

        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y년 %m월 %d일")

        message = f"📊 <b>{date_str} 일일 요약</b>\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        # ETF Summary
        if 'etf' in summary_data:
            message += "📈 <b>ETF 분석</b>\n"
            message += f"   실행 횟수: {summary_data['etf'].get('runs', 0)}회\n"
            message += f"   추천 종목: {summary_data['etf'].get('recommendations', 0)}개\n\n"

        # News Summary
        if 'news' in summary_data:
            message += "📰 <b>뉴스 수집</b>\n"
            message += f"   수집 기사: {summary_data['news'].get('articles', 0)}개\n"
            message += f"   카테고리: {summary_data['news'].get('categories', 0)}개\n\n"

        # Content Summary
        if 'content' in summary_data:
            message += "✍️ <b>콘텐츠 생성</b>\n"
            message += f"   생성 콘텐츠: {summary_data['content'].get('items', 0)}개\n\n"

        # System Health
        if 'system' in summary_data:
            message += "⚙️ <b>시스템 상태</b>\n"
            message += f"   가동 시간: {summary_data['system'].get('uptime', 'N/A')}\n"
            message += f"   오류 발생: {summary_data['system'].get('errors', 0)}건\n\n"

        message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"🕐 생성시각: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_message(message)

    def send_beauty_news(self, news_items: List[Dict[str, Any]]) -> bool:
        """Send beauty industry news from Japan"""
        return self.send_news_report(news_items, category="화장품(일본)")

    def send_display_news(self, news_items: List[Dict[str, Any]]) -> bool:
        """Send display industry news"""
        return self.send_news_report(news_items, category="디스플레이")

    def send_semiconductor_news(self, news_items: List[Dict[str, Any]]) -> bool:
        """Send semiconductor/robot/bio news"""
        return self.send_news_report(news_items, category="반도체/로봇/바이오")


# Singleton instance
_bot_instance: Optional[TelegramBot] = None


def get_telegram_bot() -> TelegramBot:
    """Get or create Telegram bot instance"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = TelegramBot()
    return _bot_instance


# Example usage
if __name__ == "__main__":
    # Test bot
    bot = get_telegram_bot()

    # Test ETF report
    sample_etf_data = [
        {
            'ticker': '069500.KS',
            'name': 'KODEX 200',
            'change_pct': 3.2,
            'stochastic': 65.8,
            'signal': 'BUY'
        },
        {
            'ticker': '102110.KS',
            'name': 'TIGER 200',
            'change_pct': 2.8,
            'stochastic': 62.1,
            'signal': 'WATCH'
        }
    ]

    bot.send_etf_report(sample_etf_data)

    # Test news report
    sample_news = [
        {
            'title': 'AI 기술 발전으로 반도체 수요 급증',
            'source': 'Naver News',
            'url': 'https://news.naver.com',
            'sentiment': 'positive'
        }
    ]

    bot.send_news_report(sample_news, category="IT")
