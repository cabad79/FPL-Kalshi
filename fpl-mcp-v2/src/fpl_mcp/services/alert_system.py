"""Automated alert and notification system for squad management."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of alerts."""

    TRANSFER_RUMOR = "transfer_rumor"
    TRANSFER_CONFIRMED = "transfer_confirmed"
    INJURY_ALERT = "injury_alert"
    FORM_DROP = "form_drop"
    FIXTURE_HARD = "fixture_hard"
    SQUAD_GENERATION_READY = "squad_generation_ready"
    DEADLINE_APPROACHING = "deadline_approaching"
    PRESEASON_MONITORING = "preseason_monitoring"
    CAPTAIN_RECOMMENDATION = "captain_recommendation"
    MANUAL_REVIEW_NEEDED = "manual_review_needed"


@dataclass
class Alert:
    """Individual alert."""

    alert_id: str
    alert_type: AlertType
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    gameweek: int | None = None
    player_ids: list[int] | None = None
    action_required: bool = False
    action_deadline: datetime | None = None
    auto_dismiss_after: timedelta | None = None


@dataclass
class ScheduledTask:
    """Scheduled automated task."""

    task_id: str
    task_name: str
    description: str
    scheduled_time: datetime
    priority: int = 3
    gameweek: int | None = None
    action: Callable | None = None
    status: str = "pending"


class AlertSystem:
    """Manages alerts and notifications."""

    def __init__(self):
        self.alerts: dict[str, Alert] = {}
        self.tasks: dict[str, ScheduledTask] = {}

    def create_alert(
        self,
        alert_type: AlertType,
        level: AlertLevel,
        title: str,
        message: str,
        gameweek: int | None = None,
        action_required: bool = False,
        action_deadline: datetime | None = None,
    ) -> Alert:
        """Create and register a new alert."""
        alert_id = f"{alert_type.value}_{datetime.now().timestamp()}"
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            gameweek=gameweek,
            action_required=action_required,
            action_deadline=action_deadline,
        )
        self.alerts[alert_id] = alert
        logger.info(f"Alert created: {title}")
        return alert

    def dismiss_alert(self, alert_id: str) -> None:
        """Dismiss an alert."""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Alert dismissed: {alert_id}")

    def get_active_alerts(self, level: AlertLevel | None = None) -> list[Alert]:
        """Get all active alerts, optionally filtered by level."""
        alerts = list(self.alerts.values())
        if level:
            alerts = [a for a in alerts if a.level == level]
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

    def get_action_required_alerts(self) -> list[Alert]:
        """Get alerts requiring manager action."""
        return [a for a in self.alerts.values() if a.action_required]

    def schedule_task(
        self,
        task_name: str,
        description: str,
        scheduled_time: datetime,
        priority: int = 3,
        gameweek: int | None = None,
    ) -> ScheduledTask:
        """Schedule an automated task."""
        task_id = f"{task_name}_{datetime.now().timestamp()}"
        task = ScheduledTask(
            task_id=task_id,
            task_name=task_name,
            description=description,
            scheduled_time=scheduled_time,
            priority=priority,
            gameweek=gameweek,
        )
        self.tasks[task_id] = task
        logger.info(f"Task scheduled: {task_name} for {scheduled_time}")
        return task

    def mark_task_completed(self, task_id: str) -> None:
        """Mark a task as completed."""
        if task_id in self.tasks:
            self.tasks[task_id].status = "completed"
            logger.info(f"Task completed: {self.tasks[task_id].task_name}")


class SeasonAlertScheduler:
    """Manages the complete season alert schedule."""

    def __init__(self):
        self.alert_system = AlertSystem()
        self.gw1_deadline = datetime(2026, 8, 22, 11, 0)  # Friday 11:00 GMT

    def create_season_schedule(self) -> dict[str, list[ScheduledTask]]:
        """Create complete alert schedule for 38-GW season."""
        schedule = {}

        # ======================================================================
        # PRE-SEASON ALERTS (GW1 Preparation)
        # ======================================================================
        schedule["pre_season"] = [
            # Aug 13: Urgent - Verify N.Jackson transfer
            self.alert_system.schedule_task(
                task_name="verify_njackson_transfer",
                description="🚨 URGENT: Check if N.Jackson transfer is real or rumor",
                scheduled_time=datetime(2026, 8, 13, 9, 0),
                priority=1,  # CRITICAL
                gameweek=1,
            ),
            # Aug 14: Monitor transfer confirmation
            self.alert_system.schedule_task(
                task_name="njackson_final_confirmation",
                description="Check N.Jackson transfer status - final decision point",
                scheduled_time=datetime(2026, 8, 14, 10, 0),
                priority=2,  # HIGH
                gameweek=1,
            ),
            # Aug 17: Preseason review deadline
            self.alert_system.schedule_task(
                task_name="preseason_lineup_verification",
                description="Verify all GW1 squad players in preseason matches",
                scheduled_time=datetime(2026, 8, 17, 10, 0),
                priority=2,
                gameweek=1,
            ),
            # Aug 19: Final squad adjustments
            self.alert_system.schedule_task(
                task_name="final_squad_adjustments",
                description="Last chance to adjust squad before GW1 deadline",
                scheduled_time=datetime(2026, 8, 19, 18, 0),
                priority=1,
                gameweek=1,
            ),
            # Aug 20: Auto-generate GW1 squad
            self.alert_system.schedule_task(
                task_name="auto_generate_gw1_squad",
                description="🤖 AUTO: Generate GW1 squad report (2 days before deadline)",
                scheduled_time=datetime(2026, 8, 20, 10, 0),
                priority=1,
                gameweek=1,
            ),
            # Aug 21: Final review before deadline
            self.alert_system.schedule_task(
                task_name="gw1_final_review",
                description="Final form/injury check before GW1 submission",
                scheduled_time=datetime(2026, 8, 21, 10, 0),
                priority=2,
                gameweek=1,
            ),
            # Aug 22 10:50: Deadline reminder
            self.alert_system.schedule_task(
                task_name="gw1_submit_squad",
                description="🔴 SUBMIT SQUAD - GW1 deadline in 10 minutes!",
                scheduled_time=datetime(2026, 8, 22, 10, 50),
                priority=1,
                gameweek=1,
            ),
        ]

        # ======================================================================
        # WEEKLY SCHEDULE (Repeating for GW2-38)
        # ======================================================================
        weekly_pattern = [
            # Monday: Analyze previous GW results
            {"day_offset": -4, "time": (9, 0), "name": "analyze_previous_gw"},
            # Wednesday: Auto-generate squad
            {"day_offset": -2, "time": (10, 0), "name": "auto_generate_squad"},
            # Thursday: Transfer monitoring
            {"day_offset": -1, "time": (10, 0), "name": "monitor_transfers"},
            # Friday 10:50: Deadline reminder
            {"day_offset": 0, "time": (10, 50), "name": "submit_squad"},
        ]

        schedule["weekly"] = weekly_pattern

        return schedule

    def create_ongoing_tasks(self) -> list[ScheduledTask]:
        """Create ongoing monitoring tasks for entire season."""
        tasks = [
            # Daily: Monitor injuries and transfer rumors
            self.alert_system.schedule_task(
                task_name="daily_injury_monitor",
                description="🏥 DAILY: Check for new injury alerts and transfer rumors",
                scheduled_time=datetime(2026, 8, 13, 12, 0),
                priority=2,
            ),
            # Daily: Form updates after matches
            self.alert_system.schedule_task(
                task_name="daily_form_update",
                description="📊 DAILY: Update player form scores post-matches",
                scheduled_time=datetime(2026, 8, 13, 18, 0),
                priority=2,
            ),
            # Every 6 hours: Transfer market monitoring
            self.alert_system.schedule_task(
                task_name="transfer_market_monitor",
                description="💰 6-HOURLY: Monitor transfer market activity",
                scheduled_time=datetime(2026, 8, 13, 6, 0),
                priority=3,
            ),
        ]
        return tasks


class AutomatedActions:
    """Executes automated actions triggered by alerts."""

    @staticmethod
    async def verify_njackson_transfer() -> dict[str, Any]:
        """Check N.Jackson transfer status."""
        logger.info("🚨 Executing: Verify N.Jackson transfer status")
        # Would integrate with external sources:
        # - Chelsea FC official
        # - Sky Sports
        # - Transfermarkt
        # - r/FantasyPL
        return {"status": "pending_verification"}

    @staticmethod
    async def generate_weekly_squad(gameweek: int) -> dict[str, Any]:
        """Auto-generate squad for gameweek."""
        logger.info(f"🤖 Executing: Generate squad for GW{gameweek}")
        # Would call WeeklySquadGenerator
        return {"gameweek": gameweek, "status": "generated"}

    @staticmethod
    async def monitor_injuries_and_transfers() -> dict[str, Any]:
        """Monitor for injury/transfer alerts."""
        logger.info("🏥 Executing: Monitor injuries and transfers")
        # Would scan:
        # - Official team news
        # - Reddit r/FantasyPL
        # - Transfermarkt
        # - Twitter alerts
        return {"new_alerts": 0}

    @staticmethod
    async def update_form_scores() -> dict[str, Any]:
        """Update player form after GW results."""
        logger.info("📊 Executing: Update player form scores")
        # Would parse match results and calculate form
        return {"players_updated": 0}

    @staticmethod
    async def final_squad_review() -> dict[str, Any]:
        """Execute final squad review before deadline."""
        logger.info("🔍 Executing: Final squad review")
        # Would verify:
        # - Lineup confirmations
        # - Late injuries
        # - Form updates
        return {"review_complete": True}


class NotificationManager:
    """Sends notifications to manager."""

    NOTIFICATION_CHANNELS = {
        "cli": "Print to terminal",
        "email": "Send email notification",
        "webhook": "Send to external webhook",
        "file": "Write to alert log file",
    }

    @staticmethod
    def send_notification(alert: Alert, channels: list[str] = ["cli"]) -> None:
        """Send alert notification through specified channels."""
        message = f"""
        ╔═══════════════════════════════════════════════════════════════╗
        ║ {alert.level.value.upper(): ^61} ║
        ║ {alert.title: ^61} ║
        ╚═══════════════════════════════════════════════════════════════╝

        Type: {alert.alert_type.value}
        Time: {alert.timestamp.isoformat()}
        GW: {alert.gameweek or 'N/A'}

        {alert.message}

        Action Required: {'YES ⚠️' if alert.action_required else 'No'}
        Deadline: {alert.action_deadline or 'N/A'}
        """

        for channel in channels:
            if channel == "cli":
                print(message)
            elif channel == "email":
                logger.info(f"Sending email: {alert.title}")
            elif channel == "webhook":
                logger.info(f"Posting to webhook: {alert.title}")
            elif channel == "file":
                with open("/tmp/fpl_alerts.log", "a") as f:
                    f.write(message + "\n")


# ============================================================================
# ALERT TEMPLATES FOR COMMON SCENARIOS
# ============================================================================

ALERT_TEMPLATES = {
    "njackson_transfer_rumor": {
        "type": AlertType.TRANSFER_RUMOR,
        "level": AlertLevel.CRITICAL,
        "title": "🚨 N.Jackson Transfer Rumor - URGENT",
        "message": """
N.Jackson (Chelsea, 0.4% owned) may be transferred.

ACTION REQUIRED:
1. Verify transfer status (official sources)
2. Check Sky Sports transfer news
3. Monitor Transfermarkt
4. Review r/FantasyPL transfer thread

IF CONFIRMED:
→ Replace with Toney (Brentford) £6.5m
→ Same price point
→ No budget impact
→ Ownership: 8.2%

DEADLINE: Aug 19, 23:59 GMT
        """,
        "action_required": True,
    },
    "squad_generation_ready": {
        "type": AlertType.SQUAD_GENERATION_READY,
        "level": AlertLevel.INFO,
        "title": "✅ Squad Report Generated",
        "message": """
Weekly squad report generated and ready for review.

NEXT STEPS:
1. Review squad composition
2. Check transfer recommendations
3. Verify fixture difficulty
4. Confirm lineup probability
5. Make final adjustments if needed

DEADLINE: Friday 11:00 GMT
        """,
        "action_required": False,
    },
    "deadline_approaching": {
        "type": AlertType.DEADLINE_APPROACHING,
        "level": AlertLevel.WARNING,
        "title": "⏰ GW Deadline in 10 Minutes",
        "message": """
URGENT: Squad submission deadline is in 10 minutes!

FINAL CHECKLIST:
□ Captain selected
□ No injured/suspended players
□ Budget valid
□ 15 players total
□ Form/news double-checked

SUBMIT NOW to avoid missing deadline!
        """,
        "action_required": True,
    },
}
