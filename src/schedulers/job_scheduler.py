"""
Job Scheduler for Daily Automated Intelligence Platform (DAIP)
Manages scheduled tasks using APScheduler
"""
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime, time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from src.config import settings, ETFConfig, NewsConfig, ContentConfig
from src.logger import setup_logger

logger = setup_logger("daip.scheduler")


class JobScheduler:
    """Main job scheduler for DAIP services"""

    def __init__(self, timezone: Optional[str] = None):
        """
        Initialize job scheduler

        Args:
            timezone: Timezone for scheduling (default: Asia/Seoul)
        """
        self.timezone = pytz.timezone(timezone or settings.timezone)
        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self.jobs: Dict[str, Any] = {}

        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )

        logger.info(f"Job scheduler initialized with timezone: {self.timezone}")

    def _job_executed_listener(self, event):
        """Listener for successful job execution"""
        logger.info(f"Job {event.job_id} executed successfully")

    def _job_error_listener(self, event):
        """Listener for job execution errors"""
        logger.error(f"Job {event.job_id} failed with exception: {event.exception}")

    def add_job(
        self,
        func: Callable,
        job_id: str,
        trigger_type: str = "cron",
        **trigger_args
    ) -> bool:
        """
        Add a job to the scheduler

        Args:
            func: Function to execute
            job_id: Unique job identifier
            trigger_type: Trigger type (cron, interval, date)
            **trigger_args: Trigger-specific arguments

        Returns:
            True if job added successfully
        """
        try:
            if job_id in self.jobs:
                logger.warning(f"Job {job_id} already exists, replacing it")
                self.remove_job(job_id)

            job = self.scheduler.add_job(
                func,
                trigger_type,
                id=job_id,
                **trigger_args
            )
            self.jobs[job_id] = job
            logger.info(f"Added job: {job_id} with trigger: {trigger_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to add job {job_id}: {str(e)}")
            return False

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        day_of_week: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Add a cron-style scheduled job

        Args:
            func: Function to execute
            job_id: Unique job identifier
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            day_of_week: Day of week (mon,tue,wed,thu,fri,sat,sun)
            **kwargs: Additional cron arguments

        Returns:
            True if job added successfully
        """
        return self.add_job(
            func,
            job_id,
            trigger_type="cron",
            hour=hour,
            minute=minute,
            day_of_week=day_of_week,
            **kwargs
        )

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        **kwargs
    ) -> bool:
        """
        Add an interval-based job

        Args:
            func: Function to execute
            job_id: Unique job identifier
            seconds: Interval in seconds
            minutes: Interval in minutes
            hours: Interval in hours
            **kwargs: Additional interval arguments

        Returns:
            True if job added successfully
        """
        return self.add_job(
            func,
            job_id,
            trigger_type="interval",
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            **kwargs
        )

    def add_time_based_job(
        self,
        func: Callable,
        job_id: str,
        times: List[str],
        day_of_week: Optional[str] = None
    ) -> bool:
        """
        Add jobs that run at specific times

        Args:
            func: Function to execute
            job_id: Job ID prefix
            times: List of times in HH:MM format
            day_of_week: Optional day of week filter

        Returns:
            True if all jobs added successfully
        """
        success = True
        for time_str in times:
            try:
                hour, minute = map(int, time_str.split(':'))
                job_id_full = f"{job_id}_{time_str.replace(':', '')}"
                result = self.add_cron_job(
                    func,
                    job_id_full,
                    hour=hour,
                    minute=minute,
                    day_of_week=day_of_week
                )
                success = success and result
            except ValueError as e:
                logger.error(f"Invalid time format {time_str}: {str(e)}")
                success = False

        return success

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a job from the scheduler

        Args:
            job_id: Job identifier

        Returns:
            True if job removed successfully
        """
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Removed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {str(e)}")
            return False

    def start(self) -> None:
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
        else:
            logger.warning("Scheduler is already running")

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the scheduler

        Args:
            wait: Wait for running jobs to complete
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler shut down")
        else:
            logger.warning("Scheduler is not running")

    def pause_job(self, job_id: str) -> bool:
        """Pause a specific job"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {str(e)}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {str(e)}")
            return False

    def get_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs"""
        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger)
            })
        return jobs_info

    def print_jobs(self) -> None:
        """Print all scheduled jobs"""
        jobs = self.get_jobs()
        if not jobs:
            logger.info("No jobs scheduled")
            return

        logger.info(f"Scheduled jobs ({len(jobs)}):")
        for job in jobs:
            logger.info(f"  - {job['id']}: next run at {job['next_run_time']}")


class ServiceScheduler:
    """High-level scheduler for DAIP services"""

    def __init__(self):
        """Initialize service scheduler"""
        self.scheduler = JobScheduler()
        logger.info("Service scheduler initialized")

    def setup_etf_service(self, etf_service_func: Callable) -> None:
        """
        Setup ETF analysis service jobs

        Args:
            etf_service_func: ETF service function to schedule
        """
        if not settings.etf_service_enabled:
            logger.info("ETF service is disabled")
            return

        # Schedule ETF jobs at specific times
        times = ETFConfig.SCHEDULE_TIMES
        self.scheduler.add_time_based_job(
            etf_service_func,
            job_id="etf_analysis",
            times=times,
            day_of_week="mon-fri"  # Only on weekdays
        )
        logger.info(f"ETF service scheduled at: {', '.join(times)}")

    def setup_news_service(self, news_service_func: Callable) -> None:
        """
        Setup news scraping service jobs

        Args:
            news_service_func: News service function to schedule
        """
        if not settings.news_service_enabled:
            logger.info("News service is disabled")
            return

        # Schedule news jobs
        times = NewsConfig.SCHEDULE_TIMES
        self.scheduler.add_time_based_job(
            news_service_func,
            job_id="news_scraping",
            times=times
        )
        logger.info(f"News service scheduled at: {', '.join(times)}")

    def setup_content_service(self, content_service_func: Callable) -> None:
        """
        Setup content generation service job

        Args:
            content_service_func: Content service function to schedule
        """
        if not settings.content_service_enabled:
            logger.info("Content service is disabled")
            return

        # Schedule daily content generation at 23:00
        hour, minute = map(int, ContentConfig.SCHEDULE_TIME.split(':'))
        self.scheduler.add_cron_job(
            content_service_func,
            job_id="content_generation",
            hour=hour,
            minute=minute
        )
        logger.info(f"Content service scheduled at: {ContentConfig.SCHEDULE_TIME}")

    def setup_beauty_news_service(self, beauty_news_func: Callable) -> None:
        """Setup beauty news service"""
        if not settings.beauty_news_enabled:
            logger.info("Beauty news service is disabled")
            return

        from src.config import BeautyNewsConfig
        self.scheduler.add_time_based_job(
            beauty_news_func,
            job_id="beauty_news",
            times=BeautyNewsConfig.SCHEDULE_TIMES
        )
        logger.info("Beauty news service scheduled")

    def setup_display_news_service(self, display_news_func: Callable) -> None:
        """Setup display news service"""
        if not settings.display_news_enabled:
            logger.info("Display news service is disabled")
            return

        from src.config import DisplayNewsConfig
        self.scheduler.add_time_based_job(
            display_news_func,
            job_id="display_news",
            times=DisplayNewsConfig.SCHEDULE_TIMES
        )
        logger.info("Display news service scheduled")

    def setup_semiconductor_news_service(self, semiconductor_news_func: Callable) -> None:
        """Setup semiconductor/robot/bio news service"""
        if not settings.semiconductor_news_enabled:
            logger.info("Semiconductor news service is disabled")
            return

        from src.config import SemiconductorNewsConfig
        self.scheduler.add_time_based_job(
            semiconductor_news_func,
            job_id="semiconductor_news",
            times=SemiconductorNewsConfig.SCHEDULE_TIMES
        )
        logger.info("Semiconductor news service scheduled")

    def start(self) -> None:
        """Start the scheduler"""
        self.scheduler.start()
        self.scheduler.print_jobs()

    def shutdown(self) -> None:
        """Shutdown the scheduler"""
        self.scheduler.shutdown()


# Example usage
if __name__ == "__main__":
    def test_job():
        logger.info("Test job executed!")

    # Create scheduler
    scheduler = JobScheduler()

    # Add a test job that runs every minute
    scheduler.add_interval_job(
        test_job,
        job_id="test_job",
        minutes=1
    )

    # Start scheduler
    scheduler.start()
    scheduler.print_jobs()

    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
