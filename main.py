"""
Main application for Daily Automated Intelligence Platform (DAIP)
Integrates all services and manages scheduling
"""
import sys
import signal
from typing import Optional
import time

from src.config import settings
from src.logger import main_logger as logger


class DAIPApplication:
    """Main DAIP application"""

    def __init__(self):
        """Initialize DAIP application"""
        logger.info("Initializing Daily Automated Intelligence Platform (DAIP)")

        self.scheduler: Optional[ServiceScheduler] = None
        self.running = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("DAIP application initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown")
        self.shutdown()
        sys.exit(0)

    def setup_scheduler(self) -> None:
        """Setup and configure the job scheduler"""
        logger.info("Setting up scheduler")

        from src.schedulers.job_scheduler import ServiceScheduler
        from src.services.etf_analyzer import run_etf_analysis
        from src.services.news_scraper import run_news_scraping
        from src.services.industry_news import (
            run_beauty_news,
            run_display_news,
            run_semiconductor_news
        )
        from src.services.content_generator import run_content_generation

        self.scheduler = ServiceScheduler()

        # Setup ETF service
        if settings.etf_service_enabled:
            logger.info("Configuring ETF analysis service")
            self.scheduler.setup_etf_service(run_etf_analysis)

        # Setup news service
        if settings.news_service_enabled:
            logger.info("Configuring news scraping service")
            self.scheduler.setup_news_service(lambda: run_news_scraping(use_mock=False))

        # Setup beauty news service
        if settings.beauty_news_enabled:
            logger.info("Configuring beauty news service")
            self.scheduler.setup_beauty_news_service(run_beauty_news)

        # Setup display news service
        if settings.display_news_enabled:
            logger.info("Configuring display news service")
            self.scheduler.setup_display_news_service(run_display_news)

        # Setup semiconductor news service
        if settings.semiconductor_news_enabled:
            logger.info("Configuring semiconductor news service")
            self.scheduler.setup_semiconductor_news_service(run_semiconductor_news)

        # Setup content generation service
        if settings.content_service_enabled:
            logger.info("Configuring content generation service")
            self.scheduler.setup_content_service(run_content_generation)

        logger.info("Scheduler setup complete")

    def send_startup_notification(self) -> None:
        """Send startup notification via Telegram"""
        try:
            from src.telegram_bot import get_telegram_bot
            bot = get_telegram_bot()
            message = """
🚀 <b>DAIP 시스템 시작</b>
━━━━━━━━━━━━━━━━━━━━━━━

시스템이 성공적으로 시작되었습니다.

<b>활성화된 서비스:</b>
"""
            if settings.etf_service_enabled:
                message += "✅ ETF 분석\n"
            if settings.news_service_enabled:
                message += "✅ 종합 뉴스\n"
            if settings.beauty_news_enabled:
                message += "✅ 화장품 뉴스\n"
            if settings.display_news_enabled:
                message += "✅ 디스플레이 뉴스\n"
            if settings.semiconductor_news_enabled:
                message += "✅ 반도체/로봇/바이오 뉴스\n"
            if settings.content_service_enabled:
                message += "✅ AI 콘텐츠 생성\n"

            message += "\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"🕐 시작 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}"

            bot.send_message(message)
            logger.info("Startup notification sent")

        except Exception as e:
            logger.error(f"Failed to send startup notification: {str(e)}")

    def start(self) -> None:
        """Start the DAIP application"""
        logger.info("Starting DAIP application")

        try:
            # Send startup notification
            self.send_startup_notification()

            # Setup and start scheduler
            self.setup_scheduler()

            if self.scheduler:
                self.scheduler.start()
                self.running = True
                logger.info("DAIP application started successfully")

                # Keep the application running
                logger.info("Application is now running. Press Ctrl+C to stop.")
                while self.running:
                    time.sleep(1)
            else:
                logger.error("Scheduler not initialized")
                sys.exit(1)

        except Exception as e:
            logger.error(f"Error starting DAIP application: {str(e)}", exc_info=True)
            sys.exit(1)

    def shutdown(self) -> None:
        """Shutdown the DAIP application"""
        if not self.running:
            return

        logger.info("Shutting down DAIP application")
        self.running = False

        try:
            # Send shutdown notification
            from src.telegram_bot import get_telegram_bot
            bot = get_telegram_bot()
            message = f"""
⚠️ <b>DAIP 시스템 종료</b>
━━━━━━━━━━━━━━━━━━━━━━━

시스템이 종료되었습니다.

🕐 종료 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
            bot.send_message(message)

        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {str(e)}")

        # Shutdown scheduler
        if self.scheduler:
            self.scheduler.shutdown()

        logger.info("DAIP application shut down complete")


def run_single_service(service_name: str) -> None:
    """
    Run a single service manually (for testing or GitHub Actions)

    Args:
        service_name: Name of service to run (etf, news, beauty, display, semiconductor, content)
    """
    logger.info(f"Running single service: {service_name}")

    try:
        if service_name == "etf":
            from src.services.etf_analyzer import run_etf_analysis
            run_etf_analysis()
        elif service_name == "news":
            from src.services.news_scraper import run_news_scraping
            run_news_scraping(use_mock=False)
        elif service_name == "beauty":
            from src.services.industry_news import run_beauty_news
            run_beauty_news()
        elif service_name == "display":
            from src.services.industry_news import run_display_news
            run_display_news()
        elif service_name == "semiconductor":
            from src.services.industry_news import run_semiconductor_news
            run_semiconductor_news()
        elif service_name == "content":
            from src.services.content_generator import run_content_generation
            run_content_generation()
        else:
            logger.error(f"Unknown service: {service_name}")
            sys.exit(1)

        logger.info(f"Service {service_name} completed successfully")

    except Exception as e:
        logger.error(f"Service {service_name} failed: {str(e)}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point"""
    logger.info("="*50)
    logger.info("Daily Automated Intelligence Platform (DAIP)")
    logger.info("Version 0.1.0")
    logger.info("="*50)

    # Check if running in single-service mode
    if len(sys.argv) > 1:
        service_name = sys.argv[1]
        run_single_service(service_name)
    else:
        # Run full application
        app = DAIPApplication()
        app.start()


if __name__ == "__main__":
    main()
