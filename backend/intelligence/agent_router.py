import logging
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AgentRouter:
    """
    Routes validated intents and entities to the existing underlying ORMA AI modules.
    Acts as the glue between the intelligence layer and the domain services.
    All inter-agent communication passes through the ResponseCoordinator.
    """
    def __init__(self):
        pass

    def _build_explainable_payload(self, status: str, action: str, data: Any, reason: str, confidence: float, memory_updates: list = None, follow_up: str = None, suggested_follow_up: str = None) -> Dict[str, Any]:
        """Builds the standardized explainable response payload."""
        return {
            "status": status,
            "action": action,
            "data": data,
            "explainability": {
                "result": status,
                "reason": reason,
                "confidence": confidence,
                "memory_updates": memory_updates or [],
                "suggested_follow_up": suggested_follow_up or follow_up
            }
        }

    async def route(self, intent: str, entities: Dict[str, Any], user_id: str, db: Session, raw_text: str = "") -> Optional[Dict[str, Any]]:
        """
        Routes the request to the appropriate domain service and returns a standardized response dict.
        """
        logger.info(f"[AgentRouter] Routing intent '{intent}' for user {user_id}")
        
        low_text = raw_text.lower() if raw_text else ""
        is_query = any(w in low_text for w in ["did i", "do i", "what", "which", "when", "have i", "any", "?", "status", "due", "take", "schedule", "pending", "today", "how did"])
        
        medication_chat_intents = [
            "MEDICATION_SCHEDULE", "MEDICATION_STATUS", "MEDICATION_SUMMARY", 
            "MEDICATION_INFORMATION", "Medicine"
        ]

        if intent in medication_chat_intents:
            is_create = entities.get("action") == "create"
            if is_query or not is_create:
                return self._build_explainable_payload(
                    status="success", action="chat", data=None,
                    reason=f"Medication intent '{intent}' routed to conversational chat coordinator.", confidence=0.95
                )
            return await self._route_to_medicine_service(intent, entities, user_id, db)
            
        elif intent == "Appointment":
            if is_query or entities.get("action") != "create":
                return self._build_explainable_payload(
                    status="success", action="chat", data=None,
                    reason="Appointment query routed to conversational chat coordinator.", confidence=0.95
                )
            return await self._route_to_health_planner(intent, entities, user_id, db, event_type="doctor_appointment")
            
        elif intent == "Reminder":
            if is_query or entities.get("action") != "create":
                return self._build_explainable_payload(
                    status="success", action="chat", data=None,
                    reason="Reminder query routed to conversational chat coordinator.", confidence=0.95
                )
            return await self._route_to_health_planner(intent, entities, user_id, db, event_type="custom_reminder")
            
        elif intent == "Emergency":
            return await self._route_to_emergency(entities, user_id, db)
            
        elif intent in ["DOCUMENT_QUERY", "GREETING", "GENERAL_CONVERSATION", "Memory", "Unknown", "Settings", "Caregiver", "HealthRecord"]:
            return self._build_explainable_payload(
                status="success", action="chat", data=None,
                reason="Document query or conversational interaction routed to chat module.", confidence=0.9
            )
            
        else:
            logger.warning(f"[AgentRouter] No explicit routing defined for intent '{intent}'. Returning default.")
            return self._build_explainable_payload(
                status="success", action="chat", data=None,
                reason=f"Intent {intent} routed to default chat coordinator.", confidence=0.8
            )

    async def _route_to_medicine_service(self, intent: str, entities: Dict[str, Any], user_id: str, db: Session) -> Dict[str, Any]:
        from services.medicine_service import create_reminder, ReminderCreate
        from routes.medicine import broadcast_medicine_event
        from models.user import User

        medicine_name = entities.get("medicine_name") or entities.get("title") or "Medicine"
        reminder_time = entities.get("time") or entities.get("reminder_time") or "08:00 PM"
        dosage = entities.get("dosage") or ""
        frequency = entities.get("frequency") or "Once Daily"
        purpose = entities.get("purpose")
        notes = entities.get("notes")

        # Resolve user context
        user_obj = db.query(User).filter(User.id == str(user_id)).first()
        if not user_obj and str(user_id).isdigit():
            user_obj = db.query(User).filter(User.id == int(user_id)).first()
        tz_name = (user_obj.timezone if user_obj and user_obj.timezone else "UTC").strip()
        role = user_obj.role if user_obj and hasattr(user_obj, "role") else "elderly"
        subject_id = str(user_id)

        reminder_data = ReminderCreate(
            medicine_name=medicine_name,
            dosage=dosage,
            reminder_time=reminder_time,
            frequency=frequency,
            purpose=purpose,
            notes=notes,
            timezone=tz_name
        )

        try:
            new_reminder = create_reminder(
                db=db,
                reminder=reminder_data,
                actor_id=subject_id,
                subject_id=subject_id,
                role=role
            )
            logger.info(f"[AgentRouter] Successfully routed to MedicineService. Created MedicineReminder ID: {new_reminder.id}")

            # Broadcast real-time websocket event
            try:
                await broadcast_medicine_event(db, subject_id, {
                    "type": "medicine_created",
                    "medicine_id": new_reminder.id,
                    "medicine_name": new_reminder.medicine_name,
                    "reminder_time": new_reminder.reminder_time,
                    "message": f"New medicine {new_reminder.medicine_name} scheduled for {new_reminder.reminder_time}."
                })
            except Exception as ws_err:
                logger.warning(f"[AgentRouter] WebSocket broadcast warning: {ws_err}")

            return self._build_explainable_payload(
                status="success",
                action="created_medicine_reminder",
                data={
                    "id": new_reminder.id,
                    "medicine_name": new_reminder.medicine_name,
                    "reminder_time": new_reminder.reminder_time,
                    "frequency": new_reminder.frequency,
                    "dosage": new_reminder.dosage
                },
                reason=f"Successfully created canonical MedicineReminder for {medicine_name} at {reminder_time}.",
                confidence=0.95,
                memory_updates=[f"User has {medicine_name} scheduled at {reminder_time}"]
            )
        except Exception as e:
            logger.error(f"[AgentRouter] Failed to create MedicineReminder: {e}")
            return self._build_explainable_payload(
                status="error",
                action="error",
                data=None,
                reason=f"Database or medicine service error: {e}",
                confidence=1.0
            )

    async def _route_to_health_planner(self, intent: str, entities: Dict[str, Any], user_id: str, db: Session, event_type: str) -> Dict[str, Any]:
        from services.health_planner_service import create_health_event, HealthEventCreate
        from models.health_event import HealthEventType
        
        title = entities.get("doctor_name") or entities.get("medicine_name") or entities.get("title") or "Health Event"
        event_date = entities.get("date")
        reminder_time = entities.get("time") or "09:00 AM"
        
        try:
            enum_type = HealthEventType(event_type)
        except Exception:
            enum_type = HealthEventType.MEDICINE

        event_data = HealthEventCreate(
            event_type=enum_type,
            title=title,
            description=f"Auto-scheduled from {intent} request",
            reminder_time=reminder_time,
            event_date=event_date,
            location=entities.get("location"),
            timezone="UTC"
        )
        
        try:
            subject_id = str(user_id)
            new_event = create_health_event(
                db=db,
                event=event_data,
                actor_id=subject_id,
                subject_id=subject_id,
                role="elderly"
            )
            logger.info(f"[AgentRouter] Successfully routed to HealthPlannerService. Created ID: {new_event.id}")
            
            return self._build_explainable_payload(
                status="success", action="created_health_event",
                data={"id": new_event.id, "title": new_event.title, "type": new_event.event_type},
                reason=f"Successfully parsed entities and scheduled {event_type} event.",
                confidence=0.95,
                memory_updates=[f"User has a {event_type} scheduled at {reminder_time}"]
            )
        except Exception as e:
            logger.error(f"[AgentRouter] Failed to create health event: {e}")
            return self._build_explainable_payload(
                status="error", action="error", data=None,
                reason=f"Database or service error: {e}", confidence=1.0
            )

    async def _route_to_emergency(self, entities: Dict[str, Any], user_id: str, db: Session) -> Dict[str, Any]:
        from services.notification_service import dispatch_notification
        try:
            elder_id_str = str(user_id)
            await dispatch_notification(
                db=db,
                elder_id=elder_id_str,
                title="Emergency Alert via Voice",
                message="User requested emergency assistance via natural language.",
                priority="high"
            )
            return self._build_explainable_payload(
                status="success", action="emergency_alert_sent", data=None,
                reason="High-priority emergency intent detected and dispatched.",
                confidence=0.99,
                suggested_follow_up="Check on the user's status within 5 minutes."
            )
        except Exception as e:
            logger.error(f"[AgentRouter] Emergency routing failed: {e}")
            return self._build_explainable_payload(
                status="error", action="error", data=None,
                reason=f"Notification dispatch failed: {e}", confidence=1.0
            )

agent_router = AgentRouter()
