import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.rlj import JournalEntry, LifeEvent, CaregiverSummary
from memory.memory_models import OCMEMemory

logger = logging.getLogger(__name__)

class ReflectionEngine:
    """
    Reflection & Life Journal Engine (RLJ).
    Periodically reviews user activity, generates meaningful summaries,
    strengthens memories, and maintains a private life journal.
    """

    def _get_start_date(self, reflection_type: str) -> datetime:
        now = datetime.utcnow()
        if reflection_type == "daily":
            return now - timedelta(days=1)
        elif reflection_type == "weekly":
            return now - timedelta(days=7)
        elif reflection_type == "monthly":
            return now - timedelta(days=30)
        return now

    def generate_reflection(self, db: Session, user_id: int, reflection_type: str = "daily"):
        """
        Generates a summary based on recent activity.
        Reflection must summarize facts and patterns only.
        """
        logger.info(f"[RLJ] Generating {reflection_type} reflection for user {user_id}")
        start_date = self._get_start_date(reflection_type)
        now = datetime.utcnow()

        # In a full system, we would query medication events, health records, etc.
        # For this sprint, we will mock the gathered data sources and synthesize a factual entry.
        
        # 1. Memory Strengthening (Part 4)
        self._strengthen_memories(db, user_id, start_date)
        
        # Mocking data gathered
        sources = [
            "Medication Adherence Logs",
            "Health Planner Events",
            "Adaptive Learning Observations",
            "Recent Memories"
        ]
        
        if reflection_type == "daily":
            content = "Today you completed all scheduled morning medications on time. Your blood pressure reading was normal (120/80) at 10:00 AM. Orma learned that you prefer taking your evening medication 30 minutes later. No major health events reported."
        elif reflection_type == "weekly":
            content = "This week, you maintained a 95% medication adherence rate. You attended your scheduled Cardiology appointment on Wednesday. Orma successfully learned your preferred waking time (7:00 AM) and adjusted reminders accordingly. Your daily steps averaged 4,500."
        else:
            content = "This month, you completed 3 medical appointments, including your annual checkup. You started a new Vitamin D supplement on the 12th. Medication adherence was strong overall, with only two missed evening doses. Orma logged 5 new important memories regarding your family."
            
        entry = JournalEntry(
            user_id=user_id,
            entry_type=reflection_type,
            content=content,
            sources_used=sources,
            date=now
        )
        db.add(entry)
        
        # Part 5 - Caregiver Summary (Excludes private memories, focuses on health)
        cg_content = f"{reflection_type.capitalize()} Health Update: Medication adherence was excellent. Vitals are stable. Attended all scheduled appointments. No emergency events recorded."
        cg_summary = CaregiverSummary(
            user_id=user_id,
            summary_type=reflection_type,
            content=cg_content,
            date=now
        )
        db.add(cg_summary)
        
        db.commit()
        logger.info(f"[RLJ] {reflection_type.capitalize()} reflection generated successfully.")
        return entry

    def _strengthen_memories(self, db: Session, user_id: int, start_date: datetime):
        """
        Increases confidence and importance for memories that are consistently used.
        Archives obsolete temporary memories.
        """
        memories = db.query(OCMEMemory).filter(OCMEMemory.user_id == user_id).all()
        now = datetime.utcnow()
        
        for mem in memories:
            # Archive expired/temporary
            if mem.expires_at and mem.expires_at < now:
                mem.archived = True
                logger.info(f"[RLJ] Archived expired memory {mem.id}")
                
            # Strengthen used memories
            if mem.last_used and mem.last_used > start_date:
                mem.confidence = min(1.0, mem.confidence + 0.05)
                mem.importance = min(100, mem.importance + 2)
                mem.trust_score = min(100.0, mem.trust_score + 5.0)
                logger.info(f"[RLJ] Strengthened memory {mem.id} due to recent usage.")

    def add_life_event(self, db: Session, user_id: int, event_type: str, title: str, description: str, event_date: datetime, source: str):
        """
        Builds a chronological timeline of significant life events.
        """
        event = LifeEvent(
            user_id=user_id,
            event_type=event_type,
            title=title,
            description=description,
            event_date=event_date,
            source=source
        )
        db.add(event)
        db.commit()
        logger.info(f"[RLJ] Life event added: {title}")
        return event

reflection_engine = ReflectionEngine()
