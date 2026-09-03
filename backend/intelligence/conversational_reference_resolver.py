import logging
import re
import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from models.medicine import MedicineReminder
from models.user import User
from intelligence.tools import med_applies_on_date, parse_time_to_minutes, get_med_times
from intelligence.conversation_manager import conversation_manager

logger = logging.getLogger(__name__)

class ConversationalReferenceResolver:
    """
    Deterministic conversational follow-up reference resolver for ORMA AI.
    Understands when a user question refers to the immediately preceding conversation turn
    (e.g., 'What about tomorrow?', 'What medicine is that?', 'What time?', 'Did I already take that one?'),
    enforces strict medical safety (never inferring dosage from a medicine name),
    and requests clarification if an anaphoric reference is ambiguous.
    """

    def resolve(
        self,
        text: str,
        user_id: str,
        db: Session,
        history: List[Dict[str, str]],
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Attempts to resolve anaphora or elliptical follow-up references using recent conversation context.
        Returns a dict indicating whether a follow-up was recognized, and if so, whether a direct
        deterministic response is available.
        """
        if not history or len(history) < 1:
            return {"is_followup": False}

        low_text = text.lower().strip()
        last_interaction = conversation_manager.get_last_interaction_context(user_id)

        # 1. Extract referenced medicines from structured session memory or recent assistant messages
        referenced_meds = self._extract_referenced_medications(history, last_interaction, db, user_id)
        if not referenced_meds:
            return {"is_followup": False}

        # 2. Check for Medication Name vs Dosage Inquiry (Critical Medical Safety)
        # e.g., "Why the 10 is the 10 mg you mean?", "Is that 10 mg?", "Why the 10?", "Does 10 mean 10 mg?"
        dosage_safety_res = self._handle_dosage_safety_inquiry(low_text, referenced_meds, db, language)
        if dosage_safety_res:
            return dosage_safety_res

        # 3. Check for Ambiguous References (Multiple candidate medicines in recent context)
        # e.g., Previous: "You have Med A at 10 AM and Med B at 6 PM." -> "What time is that?" / "Did I take that one?"
        if len(referenced_meds) > 1 and self._is_ambiguous_reference_query(low_text):
            med_a = referenced_meds[0]
            med_b = referenced_meds[1]
            time_a = med_a.get("scheduled_time") or "scheduled time"
            time_b = med_b.get("scheduled_time") or "scheduled time"
            clarification = f"Do you mean {med_a['name']} at {time_a} or {med_b['name']} at {time_b}?"
            return {
                "is_followup": True,
                "direct_response": clarification,
                "intent": "Clarification",
                "referenced_medications": referenced_meds
            }

        # 4. Check for Tomorrow / Future Schedule Follow-Up
        # e.g., "What about tomorrow?", "What about the one tomorrow?", "Is that for tomorrow?"
        tomorrow_res = self._handle_tomorrow_followup(low_text, user_id, db, referenced_meds, language)
        if tomorrow_res:
            return tomorrow_res

        # 5. Check for Medicine Identity Follow-Up
        # e.g., "What medicine is that?", "Which one?", "Which one is that?", "What medicine do you mean?"
        identity_res = self._handle_identity_followup(low_text, referenced_meds, language)
        if identity_res:
            return identity_res

        # 6. Check for Time Follow-Up
        # e.g., "What time?", "What time is that?", "When is that?", "When?", "At what time?"
        time_res = self._handle_time_followup(low_text, referenced_meds, language)
        if time_res:
            return time_res

        # 7. Check for Status / Adherence Follow-Up
        # e.g., "Did I already take that one?", "Did I take that?", "Did I take it?", "Have I taken it?"
        status_res = self._handle_status_followup(low_text, referenced_meds, db, language)
        if status_res:
            return status_res

        return {"is_followup": False}

    def _extract_referenced_medications(
        self,
        history: List[Dict[str, str]],
        last_interaction: Optional[Dict[str, Any]],
        db: Session,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieves candidate medications from structured interaction context, falling back to
        parsing known user medications mentioned in the last assistant response.
        """
        # A. From structured session context
        if last_interaction and last_interaction.get("medications"):
            meds = last_interaction["medications"]
            if isinstance(meds, list) and len(meds) > 0:
                out = []
                for m in meds:
                    if isinstance(m, dict):
                        out.append(m)
                    elif hasattr(m, "medicine_name"):
                        out.append({
                            "id": m.id,
                            "name": m.medicine_name,
                            "dosage": getattr(m, "dosage", "") or "",
                            "scheduled_time": getattr(m, "reminder_time", ""),
                            "taken": getattr(m, "taken_status", False)
                        })
                if out:
                    return out

        # B. From the last assistant message in history
        last_assistant_msg = next((m["content"] for m in reversed(history) if m.get("role") == "assistant"), "")
        if not last_assistant_msg:
            return []

        user_str = str(user_id)
        user_meds = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
        ).all()

        found = []
        low_msg = last_assistant_msg.lower()
        is_tomorrow = any(w in low_msg for w in ["tomorrow", "നാളെ", "कल", "غدا"])

        for um in user_meds:
            if um.medicine_name and um.medicine_name.lower() in low_msg:
                found.append({
                    "id": um.id,
                    "name": um.medicine_name,
                    "dosage": um.dosage or "",
                    "scheduled_time": um.reminder_time or "",
                    "taken": um.taken_status,
                    "day": "tomorrow" if is_tomorrow else "today"
                })

        return found

    def _handle_dosage_safety_inquiry(
        self,
        low_text: str,
        referenced_meds: List[Dict[str, Any]],
        db: Session,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """
        CRITICAL MEDICAL SAFETY:
        Checks if the user asks if a number in a medicine name means milligrams (e.g. 'Why the 10 is the 10 mg you mean?').
        Never assumes dosage from name unless DB record explicitly confirms it.
        """
        # Look for patterns like "why the 10", "is 10 the 10 mg you mean", "is that 10 mg", "does 10 mean 10 mg"
        match = re.search(r'\b(?:why\s+(?:the|is\s+there\s+a)\s+(\d+)|is\s+(?:the\s+)?(\d+)\s*(?:the\s+)?(\d+)?\s*mg|is\s+that\s+(\d+)\s*mg|does\s+(\d+)\s*mean)\b', low_text)
        contains_dosage_query = match or ("why the" in low_text and "mg" in low_text) or ("is that" in low_text and "mg" in low_text)

        if not contains_dosage_query:
            return None

        # Extract the target number (e.g. 10)
        num_match = re.search(r'\b(\d+)\b', low_text)
        num_str = num_match.group(1) if num_match else "10"

        target_med = referenced_meds[0]
        med_id = target_med.get("id")
        med_name = target_med.get("name", "your medicine")

        # Query live DB record for ground truth dosage
        db_med = None
        if med_id:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.id == med_id).first()
        if not db_med:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.medicine_name == med_name).first()

        actual_dosage = (db_med.dosage if db_med and db_med.dosage else "").strip()

        # Check if actual dosage explicitly states this number with mg
        if actual_dosage and (f"{num_str} mg" in actual_dosage.lower() or f"{num_str}mg" in actual_dosage.lower() or actual_dosage.lower() == num_str):
            response = f"The prescribed dosage for {med_name} is {actual_dosage}."
        else:
            # Safe refusal to assume: The number in the name cannot be inferred as dosage
            response = (
                f"The medicine name is '{med_name}'. I can check the prescribed dosage, "
                f"but I don't want to assume that the '{num_str}' in the medicine name means {num_str} mg. "
                "Please check your prescription or consult your doctor for the exact dosage."
            )

        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_INFORMATION",
            "referenced_medications": referenced_meds
        }

    def _is_ambiguous_reference_query(self, low_text: str) -> bool:
        """Detects if query uses a singular pronoun/reference ('that', 'that one', 'what time') when multiple items exist."""
        return any(p in low_text for p in [
            "what time is that", "what time", "which one is that", "which one",
            "what medicine is that", "did i already take that one", "did i take that",
            "did i take that one", "have i taken it", "did i take it", "when is that",
            "what about it", "what about that"
        ])

    def _handle_tomorrow_followup(
        self,
        low_text: str,
        user_id: str,
        db: Session,
        referenced_meds: List[Dict[str, Any]],
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Handles follow-ups asking about tomorrow's schedule or medicine."""
        is_tomorrow_query = any(p in low_text for p in [
            "what about tomorrow", "what about the one tomorrow", "what about tomorrow's medicine",
            "is that for tomorrow", "is that tomorrow", "tomorrow?", "tomorrow",
            "how many do i have tomorrow", "നാളെയോ", "നാളത്തെ കാര്യമോ", "कल के बारे में क्या", "ماذا عن الغد"
        ])
        if not is_tomorrow_query:
            return None

        # Resolve user local date
        user_obj = db.query(User).filter(User.id == str(user_id)).first()
        import zoneinfo
        tz_name = (user_obj.timezone if user_obj and user_obj.timezone else "UTC").strip()
        try:
            user_tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            user_tz = datetime.timezone.utc

        now_local = datetime.datetime.now(user_tz)
        tomorrow_date = now_local.date() + datetime.timedelta(days=1)

        user_str = str(user_id)
        all_meds = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
        ).all()

        tomorrow_meds = [m for m in all_meds if med_applies_on_date(m, tomorrow_date)]

        if tomorrow_meds:
            tomorrow_meds_doses = []
            for tm in tomorrow_meds:
                for tt in get_med_times(tm) or ["Standard time"]:
                    mins = parse_time_to_minutes(tt)
                    tomorrow_meds_doses.append({
                        "name": tm.medicine_name,
                        "dosage": tm.dosage or "",
                        "scheduled_time": tt,
                        "minutes": mins if mins is not None else 9999
                    })
            tomorrow_meds_doses.sort(key=lambda d: d["minutes"])
            d_strs = [f"{d['name']} scheduled at {d['scheduled_time']}" for d in tomorrow_meds_doses]
            p_str = ", ".join(d_strs)
            response = f"Tomorrow you have {p_str}."
        else:
            response = "You have no medicines scheduled for tomorrow."

        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_SCHEDULE",
            "referenced_medications": referenced_meds
        }

    def _handle_identity_followup(
        self,
        low_text: str,
        referenced_meds: List[Dict[str, Any]],
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Handles questions asking to identify the referenced medicine ('What medicine is that?')."""
        is_identity_query = any(p in low_text for p in [
            "what medicine is that", "which one is that", "which one",
            "what medicine is it", "what medicine do you mean", "which medicine do you mean",
            "which one do you mean", "അത് ഏത് മരുന്നാണ്", "वह कौन सी दवा है", "ما هو ذلك الدواء"
        ])
        if not is_identity_query:
            return None

        med = referenced_meds[0]
        response = f"That medicine is {med['name']}."
        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_INFORMATION",
            "referenced_medications": referenced_meds
        }

    def _handle_time_followup(
        self,
        low_text: str,
        referenced_meds: List[Dict[str, Any]],
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Handles questions asking for the scheduled time of the referenced medicine ('What time?')."""
        is_time_query = any(p in low_text for p in [
            "what time", "what time is that", "what time is it", "when is that",
            "when is it", "at what time", "when?", "what time?", "ഏത് സമയം",
            "എപ്പോഴാണ്", "किस समय", "في أي وقت"
        ])
        if not is_time_query:
            return None

        med = referenced_meds[0]
        day_str = f" {med.get('day', 'tomorrow')}" if med.get("day") else ""
        time_str = med.get("scheduled_time") or "its scheduled time"
        response = f"{med['name']} is scheduled for {time_str}{day_str}."
        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_SCHEDULE",
            "referenced_medications": referenced_meds
        }

    def _handle_status_followup(
        self,
        low_text: str,
        referenced_meds: List[Dict[str, Any]],
        db: Session,
        language: str
    ) -> Optional[Dict[str, Any]]:
        """Handles questions asking whether the referenced medicine was taken ('Did I already take that one?')."""
        is_status_query = any(p in low_text for p in [
            "did i already take that one", "did i take that", "did i take that one",
            "did i take it", "did i take it already", "have i taken it", "have i taken that",
            "is it taken", "is that taken", "was that taken", "did i already take it",
            "ഞാൻ അത് കഴിച്ചോ", "क्या मैंने वह ले ली", "هل أخذت ذلك الدواء"
        ])
        if not is_status_query:
            return None

        med = referenced_meds[0]
        med_id = med.get("id")
        med_name = med.get("name", "that medicine")

        db_med = None
        if med_id:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.id == med_id).first()
        if not db_med:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.medicine_name == med_name).first()

        is_taken = db_med.taken_status if db_med else med.get("taken", False)

        if is_taken:
            response = f"Yes, you have already taken {med_name}."
        else:
            day_str = f" for {med.get('day', 'tomorrow')}" if med.get("day") else ""
            time_str = f" at {med.get('scheduled_time')}" if med.get("scheduled_time") else ""
            response = f"No, you have not taken {med_name} yet. It is still scheduled{day_str}{time_str}."

        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_STATUS",
            "referenced_medications": referenced_meds
        }

conversational_reference_resolver = ConversationalReferenceResolver()
