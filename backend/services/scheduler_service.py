import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import SessionLocal
from models.medicine import MedicineReminder
from models.health_event import HealthEvent
import pytz

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(
    job_defaults={
        'max_instances': 1,
        'coalesce': True,
        'misfire_grace_time': 15
    }
)

# Global list of pending reminders to be fetched by the frontend
pending_reminders = []
# Set to track which reminders have already been queued today to prevent repeats
triggered_today = set()

main_app_loop = None

def process_event(db, item, item_type):
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    tz_name = item.timezone if item.timezone else "UTC"
    try:
        local_tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        local_tz = pytz.utc
        
    local_now = now_utc.astimezone(local_tz)
    current_time_str = local_now.strftime("%I:%M %p")

    # Check frequency logic
    if hasattr(item, "frequency") and item.frequency:
        freq = item.frequency
        if freq.startswith("Weekly"):
            today_day = local_now.strftime("%A")
            if today_day not in freq:
                return
        elif freq.startswith("Monthly"):
            try:
                target_day = int(freq.split("-")[1].strip())
                if local_now.day != target_day:
                    return
            except:
                pass
        elif freq == "Alternate Days" or freq == "Alternate days":
            try:
                created_ordinal = item.created_at.toordinal()
                if (local_now.toordinal() - created_ordinal) % 2 != 0:
                    return
            except:
                pass
        elif freq == "SOS (As Needed)" or freq == "SOS":
            return

    reminder_times = [t.strip() for t in (item.reminder_time or "").split(',') if t.strip()]

    if current_time_str in reminder_times:
        trigger_key = f"{item_type}_{item.id}_{local_now.strftime('%Y-%m-%d_%H:%M')}"
        
        if trigger_key not in triggered_today:
            triggered_today.add(trigger_key)
            
            import asyncio
            from services.notification_manager import notification_manager
            
            if item_type == "medicine":
                logger.info(f"Triggering reminder for {item.medicine_name} in {tz_name}")
            else:
                logger.info(f"Triggering reminder for {item.title} in {tz_name}")
            
            item.reminder_triggered_at = datetime.utcnow()
            item.is_caregiver_notified = False
            item.caregiver_notified_at = None
            db.commit()
            
            # Route through the scalable notification manager safely on the main event loop
            if main_app_loop and main_app_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    notification_manager.notify_user(db, item, channels=['in_app', 'browser_push', 'voice']),
                    main_app_loop
                )
    
    # Escalation Check: If triggered more than 30 mins ago, still pending, and caregiver not yet notified
    triggered_at = getattr(item, "reminder_triggered_at", None)
    is_notified = getattr(item, "is_caregiver_notified", False)
    
    if triggered_at and not is_notified:
        trig_utc = triggered_at if triggered_at.tzinfo else pytz.utc.localize(triggered_at)
        time_diff = now_utc - trig_utc
        
        if time_diff.total_seconds() > 1800:
            item.is_caregiver_notified = True
            item.caregiver_notified_at = datetime.utcnow()
            item.adherence_pattern_flags = "missed"
            db.commit()
            
            logger.info(f"[CAREGIVER] Escalating missed reminder ID={item.id} (Type={item_type}) to caregiver")
            from services.notification_manager import notification_manager
            import asyncio
            if main_app_loop and main_app_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    notification_manager.escalate_missed_reminder(db, item),
                    main_app_loop
                )


def check_all_reminders():
    """
    Checks the database every 15 seconds to see if any medicines or health events are scheduled for the current minute
    based on the user's specific timezone.
    """
    db = SessionLocal()
    try:
        # Check medicines
        medicines = db.query(MedicineReminder).filter(
            MedicineReminder.taken_status == False
        ).all()
        for med in medicines:
            process_event(db, med, "medicine")
            
        # Check health events
        events = db.query(HealthEvent).filter(
            HealthEvent.status == False
        ).all()
        for ev in events:
            process_event(db, ev, "health_event")

    except Exception as e:
        logger.error(f"Error checking reminders: {e}")
        db.rollback()
    finally:
        db.close()


def run_automated_backup():
    """
    Executes automated point-in-time SQLite backup on scheduled interval.
    """
    try:
        from database import engine
        if engine.dialect.name != "sqlite":
            logger.info("[AUTOMATED-BACKUP] Active database is PostgreSQL. Local SQLite backup bypassed (managed via Supabase).")
            return
        from infrastructure.backup_service import BackupService
        logger.info("[AUTOMATED-BACKUP] Scheduled database backup triggering...")
        res = BackupService.create_backup()
        logger.info(f"[AUTOMATED-BACKUP] Successfully created backup {res['filename']} ({res['file_size_bytes']} bytes)")
    except Exception as e:
        logger.error(f"[AUTOMATED-BACKUP ERROR] Automated backup failed: {type(e).__name__} ({str(e)})")


def start_scheduler(loop=None):
    """
    Starts the APScheduler background jobs.
    """
    global main_app_loop
    if loop:
        main_app_loop = loop

    if not scheduler.running:
        # Check every 15 seconds
        scheduler.add_job(check_all_reminders, 'interval', seconds=15, id='check_reminders', replace_existing=True)

        # Automated SQLite database backup (default: every 6 hours for SQLite)
        import os
        try:
            from database import engine
            if engine.dialect.name == "sqlite":
                backup_hours = int(os.getenv("BACKUP_INTERVAL_HOURS", "6"))
                if backup_hours > 0:
                    scheduler.add_job(
                        run_automated_backup,
                        'interval',
                        hours=backup_hours,
                        id='automated_db_backup',
                        replace_existing=True
                    )
                    logger.info(f"[AUTOMATED-BACKUP] Registered background SQLite backup job every {backup_hours} hours.")
            else:
                logger.info("[AUTOMATED-BACKUP] Database is PostgreSQL; skipping local SQLite backup schedule (managed externally).")
        except Exception as e:
            logger.warning(f"[AUTOMATED-BACKUP] Failed to register backup job: {e}")

        scheduler.start()
        logger.info("Background reminder scheduler started.")


def stop_scheduler():
    """
    Stops the APScheduler background jobs on FastAPI shutdown/reload.
    """
    global main_app_loop
    main_app_loop = None
    if scheduler.running:
        try:
            scheduler.shutdown(wait=False)
            logger.info("Background reminder scheduler stopped.")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")


def get_and_clear_pending_reminders():
    """
    Called by the FastAPI route to get the reminders and immediately clear them
    so the frontend doesn't get duplicate popups.
    """
    global pending_reminders
    reminders = list(pending_reminders)
    pending_reminders.clear()
    return reminders
