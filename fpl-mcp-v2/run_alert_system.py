#!/usr/bin/env python3
"""Run the FPL alert system scheduler."""

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fpl_mcp.services.alert_system import SeasonAlertScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def job_callback(task_name: str) -> None:
    """Callback for scheduled tasks."""
    logger.info(f"🔔 Task executed: {task_name}")


def main():
    """Initialize and run the alert system."""
    logger.info("🚀 FPL Alert System Starting...")
    logger.info(f"⏰ Current time: {datetime.now()}")

    # Create season scheduler
    season_scheduler = SeasonAlertScheduler()
    schedule = season_scheduler.create_season_schedule()

    logger.info(f"📅 Pre-season tasks scheduled: {len(schedule['pre_season'])}")
    logger.info(f"📅 Weekly pattern: {len(schedule['weekly'])} tasks per gameweek")

    # Create APScheduler scheduler
    scheduler = BackgroundScheduler()

    # Schedule all pre-season tasks
    for task in schedule['pre_season']:
        logger.info(f"📌 Scheduled: {task.task_name} at {task.scheduled_time}")
        scheduler.add_job(
            job_callback,
            'date',
            run_date=task.scheduled_time,
            args=[task.task_name],
            id=task.task_id
        )

    scheduler.start()

    logger.info("✅ Alert system running (Press Ctrl+C to stop)")

    try:
        while True:
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
