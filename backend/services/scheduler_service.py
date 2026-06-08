import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from database import SessionLocal
from models.medicine import MedicineReminder

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

# Global list of pending reminders to be fetched by the frontend
pending_reminders = []
# Set to track which reminders have already been queued today to prevent repeats
triggered_today = set()

def check_medicine_reminders():
    """
    Checks the database every 15 seconds to see if any medicines are scheduled for the current minute.
    If so, adds them to the pending_reminders queue for the frontend to pick up.
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        current_time_str = now.strftime("%I:%M %p") # Format matches frontend: e.g. "08:30 AM"
        
        # Reset the triggered_today set at midnight (roughly, or just check the current time)
        if current_time_str == "12:00 AM":
            triggered_today.clear()
            
        medicines = db.query(MedicineReminder).filter(
            MedicineReminder.reminder_time == current_time_str,
            MedicineReminder.taken_status == False
        ).all()
        
        for med in medicines:
            # Create a unique key for today's reminder
            trigger_key = f"{med.id}_{now.strftime('%Y-%m-%d_%H:%M')}"
            
            if trigger_key not in triggered_today:
                # We haven't triggered this one in this exact minute yet
                triggered_today.add(trigger_key)
                
                # Check if it's already in the pending list
                if not any(r['id'] == med.id for r in pending_reminders):
                    logger.info(f"Triggering reminder for {med.medicine_name}")
                    
                    # Update database with trigger timestamp
                    med.reminder_triggered_at = datetime.utcnow()
                    db.commit()
                    
                    pending_reminders.append({
                        "id": med.id,
                        "medicine_name": med.medicine_name,
                        "dosage": med.dosage,
                        "message_en": f"It's time to take your {med.medicine_name}.",
                        "message_ml": f"ഇപ്പോൾ {med.medicine_name} മരുന്ന് എടുക്കണം."
                    })
    except Exception as e:
        logger.error(f"Error checking reminders: {e}")
    finally:
        db.close()

def start_scheduler():
    """
    Starts the APScheduler background jobs.
    """
    if not scheduler.running:
        # Check every 15 seconds
        scheduler.add_job(check_medicine_reminders, 'interval', seconds=15, id='check_reminders', replace_existing=True)
        scheduler.start()
        logger.info("Background reminder scheduler started.")

def get_and_clear_pending_reminders():
    """
    Called by the FastAPI route to get the reminders and immediately clear them
    so the frontend doesn't get duplicate popups.
    """
    global pending_reminders
    reminders = list(pending_reminders)
    pending_reminders.clear()
    return reminders
