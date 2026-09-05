import logging
import re
import datetime
import pytz
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from models.medicine import MedicineReminder
from models.user import User
from intelligence.tools import med_applies_on_date, parse_time_to_minutes, get_med_times, is_med_in_time_period
from intelligence.conversation_manager import conversation_manager
from services.medicine_service import resolve_medication_daily_status

logger = logging.getLogger(__name__)

class ConversationalReferenceResolver:
    """
    Deterministic conversational understanding, reference resolution, and follow-up engine for ORMA AI.
    Understands user purpose, resolves anaphora (it, that, that one, the second one, the morning one),
    handles conversational acknowledgments (Okay, Yeah, Got it, ശരി), thanks, repeat requests,
    recalls recent conversation turns, handles user corrections, detects ambiguous references and asks
    concise clarifications, and grounds all medication facts in live SQLite database records.
    Supports both English and natural Malayalam (മലയാളം).
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
        Main resolution pipeline for conversational turns.
        """
        low_text = text.lower().strip()
        clean_text = re.sub(r"[^\w\s\u0D00-\u0D7F]", "", low_text).strip()
        is_ml = (language and language.lower().startswith("ml")) or bool(re.search(r"[\u0D00-\u0D7F]", text))

        # ---------------------------------------------------------------------
        # 1. PURE CONVERSATIONAL ACKNOWLEDGMENTS ("Okay", "Yeah", "Got it", "ശരി", "Right", "Fine")
        # ---------------------------------------------------------------------
        question_words = ["what", "when", "how", "where", "which", "is", "did", "can", "could", "tell", "show", "schedule", "appointment", "എന്താണ്", "എപ്പോഴാണ്", "ഷെഡ്യൂൾ"]
        medication_keywords = [
            "medicine", "medicines", "medication", "medications", "pill", "pills", "tablet", "tablets", 
            "syrup", "dose", "dosage", "adherence", "മരുന്ന്", "മരുന്നുകൾ"
        ]
        has_subsequent_question = any(qw in low_text for qw in question_words)
        has_med_keyword = any(w in low_text for w in medication_keywords)

        ack_words = {
            "okay", "ok", "yeah", "yes", "alright", "fine", "got it", "understood",
            "right", "yep", "yup", "hmm", "ah", "sure", "cool", "perfect", "good", "great",
            "ശരി", "തീർച്ചയായും", "മനസ്സിലായി", "ശരിയാണ്", "അതെ", "ഓക്കെ", "ശരി ഓർമ", "ആ ശരി", "ശരി നന്ദി"
        }
        
        is_pure_ack = False
        if not has_subsequent_question and not has_med_keyword:
            if clean_text in ack_words:
                is_pure_ack = True
            elif re.match(r"^(okay|ok|yeah|yes|alright|right|fine|got it|hmm|ah|ശരി|അതെ|ഓക്കെ)(\s+(then|dear|orma|thanks|okay|got\s+it|understood|ആ|ഓർമ|അത്\s+മനസ്സിലായി))*$", clean_text):
                is_pure_ack = True
            elif clean_text in ["thats fine", "that's fine", "sounds good", "okay thanks", "ok thanks", "that is fine", "yeah okay", "ah okay", "hmm okay", "right okay", "okay got it", "ok got it"]:
                is_pure_ack = True

        if is_pure_ack:
            ack_reply = "ശരി." if is_ml else "Alright."
            return {
                "is_followup": True,
                "direct_response": ack_reply,
                "intent": "ACKNOWLEDGMENT",
                "execution_mode": "DIRECT"
            }

        # ---------------------------------------------------------------------
        # 2. THANKS & FAREWELL
        # ---------------------------------------------------------------------
        thanks_phrases = [
            "thanks", "thank you", "thanks a lot", "thank you very much", "thank you so much",
            "many thanks", "thank you orma", "thanks orma", "thats helpful thanks", "that's helpful thanks",
            "helpful thanks", "നന്ദി", "വളരെ നന്ദി", "നന്ദി ഓർമ"
        ]
        is_pure_thanks = (clean_text in thanks_phrases or any(clean_text.startswith(p + " ") or clean_text.endswith(" " + p) for p in ["thanks", "thank you", "നന്ദി"])) and not has_subsequent_question and not has_med_keyword
        if is_pure_thanks:
            thanks_reply = "തീർച്ചയായും, സന്തോഷം!" if is_ml else "You're welcome!"
            return {
                "is_followup": True,
                "direct_response": thanks_reply,
                "intent": "THANKS",
                "execution_mode": "DIRECT"
            }

        farewell_phrases = [
            "bye", "goodbye", "see you", "good night", "bye orma", "goodbye orma",
            "വിട", "ശുഭരാത്രി"
        ]
        if clean_text in farewell_phrases:
            farewell_reply = "വിട, ശ്രദ്ധിക്കുക!" if is_ml else "Goodbye! Take care."
            return {
                "is_followup": True,
                "direct_response": farewell_reply,
                "intent": "FAREWELL",
                "execution_mode": "DIRECT"
            }

        # ---------------------------------------------------------------------
        # 3. CONVERSATION RECALL ("What did I just tell you?")
        # (Evaluated before repetition so that "ഞാൻ എന്താണ് പറഞ്ഞത്" is treated as recall, not repetition)
        # ---------------------------------------------------------------------
        recall_patterns = [
            "what did i just tell you", "what did i tell you", "what did i just say", "what did i say",
            "what was i saying", "what did i tell you just now", "do you remember what i said",
            "ഞാൻ എന്താണ് പറഞ്ഞത്", "ഞാൻ ഇപ്പോൾ എന്താണ് പറഞ്ഞത്", "ഞാൻ പറഞ്ഞത് ഓർക്കുന്നുണ്ടോ"
        ]
        if any(p in low_text for p in recall_patterns):
            user_turns = [m["content"] for m in history if m.get("role") in ("user", "User") and m.get("content", "").strip().lower() != low_text]
            if user_turns:
                last_user_turn = user_turns[-1]
                recall_reply = f"നിങ്ങൾ അവസാനം പറഞ്ഞത്: \"{last_user_turn}\" എന്നാണ്." if is_ml else f"You just told me: \"{last_user_turn}\"."
            else:
                recall_reply = "നമ്മൾ ഇപ്പോൾ സംസാരിച്ചു തുടങ്ങിയിട്ടേ ഉള്ളൂ." if is_ml else "We just started our conversation. What would you like to talk about?"
            return {
                "is_followup": True,
                "direct_response": recall_reply,
                "intent": "CONVERSATION_RECALL",
                "execution_mode": "DIRECT"
            }

        # ---------------------------------------------------------------------
        # 4. REPETITION REQUEST ("Can you tell me that again?", "Repeat that")
        # ---------------------------------------------------------------------
        repeat_patterns = [
            "repeat that", "can you repeat that", "could you repeat that", "can you repeat",
            "can you tell me that again", "tell me that again", "say that again", "what did you say",
            "tell me again", "repeat please", "could you say that again", "i didn't hear you", "didnt hear you",
            "did not hear you", "one more time", "again please", "once more", "say again",
            "can you repeat അത്",
            "ഒന്നുകൂടി പറയാമോ", "ഒന്ന് കൂടി പറയാമോ", "ഒന്നുകൂടി പറയൂ", "വീണ്ടും പറയാമോ", "ഒരിക്കൽ കൂടി"
        ]
        if any(p in low_text for p in repeat_patterns) or ("എന്താണ് പറഞ്ഞത്" in low_text and "ഞാൻ" not in low_text) or clean_text in ["again", "again?"]:
            trivial_acks = {"alright.", "okay.", "got it.", "ശരി.", "alright", "okay", "got it", "ശരി"}
            last_assistant_msg = next((m["content"] for m in reversed(history) if m.get("role") in ("assistant", "Orma") and m.get("content", "").strip().lower() not in trivial_acks), "")
            if not last_assistant_msg:
                last_assistant_msg = next((m["content"] for m in reversed(history) if m.get("role") in ("assistant", "Orma")), "")
            if last_assistant_msg:
                repeat_reply = f"തീർച്ചയായും: {last_assistant_msg}" if is_ml else f"Certainly: {last_assistant_msg}"
            else:
                repeat_reply = "നിങ്ങളെ സഹായിക്കാൻ ഞാൻ ഇവിടെയുണ്ട്. എന്ത് സഹായമാണ് വേണ്ടത്?" if is_ml else "I said that I am here and ready to help you."
            return {
                "is_followup": True,
                "direct_response": repeat_reply,
                "intent": "REPEAT_REQUEST",
                "execution_mode": "DIRECT"
            }

        # ---------------------------------------------------------------------
        # 5. USER CORRECTIONS ("No, I meant the morning medicine")
        # ---------------------------------------------------------------------
        correction_res = self._handle_user_correction(low_text, user_id, db, is_ml)
        if correction_res:
            return correction_res

        # ---------------------------------------------------------------------
        # 6. EXTRACT CANDIDATE MEDICINES FOR FOLLOW-UPS
        # ---------------------------------------------------------------------
        last_interaction = conversation_manager.get_last_interaction_context(user_id)
        referenced_meds = self._extract_referenced_medications(history, last_interaction, db, user_id)

        # ---------------------------------------------------------------------
        # 6b. MEDICATION TAKEN CONFIRMATION ("I already took that medicine", "ഞാൻ അത് കഴിച്ചു", "mark it as taken")
        # ---------------------------------------------------------------------
        taken_res = self._handle_taken_confirmation(low_text, user_id, db, referenced_meds, is_ml)
        if taken_res:
            return taken_res

        # ---------------------------------------------------------------------
        # 6c. DIRECT STATUS INQUIRY ("Did I take it?", "Have I taken that?", "Is it marked as taken?")
        # ---------------------------------------------------------------------
        status_inquiry_res = self._handle_status_followup(low_text, referenced_meds, db, is_ml, user_id=user_id)
        if status_inquiry_res:
            return status_inquiry_res

        # ---------------------------------------------------------------------
        # 7. TOMORROW / FUTURE SCHEDULE FOLLOW-UP ("What about tomorrow?")
        # ---------------------------------------------------------------------
        tomorrow_res = self._handle_tomorrow_followup(low_text, user_id, db, referenced_meds, is_ml)
        if tomorrow_res:
            return tomorrow_res

        # ---------------------------------------------------------------------
        # 8. ORDINAL & TIME-OF-DAY EXPLICIT ENTITY REFERENCES
        # e.g., "What about the second one?", "What about the morning one?", "Morning medicine ഏതാണ്?"
        # Evaluated before checking if referenced_meds is empty, so DB can be queried if needed.
        # ---------------------------------------------------------------------
        entity_ref_res = self._handle_explicit_entity_reference(low_text, referenced_meds, db, is_ml, user_id=user_id)
        if entity_ref_res:
            return entity_ref_res

        # If no active medications in context, subsequent med follow-ups do not apply
        if not referenced_meds:
            return {"is_followup": False}

        # ---------------------------------------------------------------------
        # 9. CRITICAL MEDICAL SAFETY: DOSAGE SAFETY INQUIRY
        # ---------------------------------------------------------------------
        dosage_safety_res = self._handle_dosage_safety_inquiry(low_text, referenced_meds, db, language)
        if dosage_safety_res:
            return dosage_safety_res

        # ---------------------------------------------------------------------
        # 10. AMBIGUOUS PRONOUN / REFERENCE CHECK
        # Multiple candidates in context without specific selection -> Clarify!
        # ---------------------------------------------------------------------
        if len(referenced_meds) > 1 and self._is_ambiguous_reference_query(low_text):
            med_a = referenced_meds[0]
            med_b = referenced_meds[1]
            time_a = med_a.get("scheduled_time") or "scheduled time"
            time_b = med_b.get("scheduled_time") or "scheduled time"
            if is_ml:
                clarification = f"നിങ്ങൾ {med_a['name']} ({time_a}) ആണോ {med_b['name']} ({time_b}) ആണോ ഉദ്ദേശിച്ചത്?"
            else:
                clarification = f"Do you mean {med_a['name']} at {time_a} or {med_b['name']} at {time_b}?"
            return {
                "is_followup": True,
                "direct_response": clarification,
                "intent": "Clarification",
                "execution_mode": "CLARIFICATION",
                "referenced_medications": referenced_meds
            }

        # ---------------------------------------------------------------------
        # 11. MEDICINE IDENTITY FOLLOW-UP ("What medicine is that?")
        # ---------------------------------------------------------------------
        identity_res = self._handle_identity_followup(low_text, referenced_meds, is_ml)
        if identity_res:
            return identity_res

        # ---------------------------------------------------------------------
        # 12. TIME FOLLOW-UP ("What time?", "When should I take it?")
        # ---------------------------------------------------------------------
        time_res = self._handle_time_followup(low_text, referenced_meds, is_ml)
        if time_res:
            return time_res

        # ---------------------------------------------------------------------
        # 13. STATUS / ADHERENCE FOLLOW-UP ("Did I already take that one?")
        # ---------------------------------------------------------------------
        status_res = self._handle_status_followup(low_text, referenced_meds, db, is_ml)
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
        parsing known user medications mentioned in the last assistant response in chronological order.
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
                            "taken": resolve_medication_daily_status(m)
                        })
                if out:
                    return out

        # B. From the last assistant message in history
        last_assistant_msg = next((m["content"] for m in reversed(history) if m.get("role") in ("assistant", "Orma")), "")
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
                taken_val = False if is_tomorrow else resolve_medication_daily_status(um)
                found.append({
                    "id": um.id,
                    "name": um.medicine_name,
                    "dosage": um.dosage or "",
                    "scheduled_time": um.reminder_time or "",
                    "taken": taken_val,
                    "day": "tomorrow" if is_tomorrow else "today",
                    "pos": low_msg.find(um.medicine_name.lower())
                })

        # Ensure candidates preserve the exact order they appeared in the assistant message
        found.sort(key=lambda m: m["pos"])
        for item in found:
            item.pop("pos", None)

        return found

    def _handle_user_correction(
        self,
        low_text: str,
        user_id: str,
        db: Session,
        is_ml: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Handles user conversational corrections (e.g., 'No, I meant the morning one', 'Sorry, the morning medicine').
        Updates interpretation and answers corrected request grounded in live DB.
        """
        correction_signals = [
            "no i meant", "no, i meant", "i meant the", "no the morning", "no, the morning",
            "no the evening", "no, the evening", "not that one", "no sorry i meant", "sorry, the morning",
            "sorry the morning", "i was asking about the other one", "i meant the first one", "actually no, i meant",
            "അല്ല, രാവിലെ", "അതല്ല ഞാൻ ഉദ്ദേശിച്ചത്", "അതല്ല, ഞാൻ ഉദ്ദേശിച്ചത്", "അതല്ല", "അല്ല രാവിലെ",
            "രാവിലെ ഉള്ള മരുന്നാണ് ഞാൻ ചോദിച്ചത്", "രാവിലെ കഴിക്കുന്ന മരുന്നാണ്"
        ]
        is_correction = any(s in low_text for s in correction_signals)
        if not is_correction:
            return None

        # Determine target period or ordinal from correction text
        target_period = None
        period_label = "morning"
        period_label_ml = "രാവിലത്തെ"

        if any(w in low_text for w in ["morning", "രാവിലെ", "breakfast", "am", "first", "ആദ്യത്തെ"]):
            target_period = "morning"
            period_label = "morning"
            period_label_ml = "രാവിലത്തെ"
        elif any(w in low_text for w in ["evening", "night", "വൈകുന്നേരം", "രാത്രി", "dinner", "pm", "bedtime"]):
            target_period = "evening"
            period_label = "evening"
            period_label_ml = "വൈകുന്നേരത്തെ"
        elif any(w in low_text for w in ["other", "not that", "മറ്റേത്"]):
            # Toggle from last interaction if possible
            last_interaction = conversation_manager.get_last_interaction_context(user_id)
            prev_time = ""
            if last_interaction and last_interaction.get("medications"):
                prev_time = (last_interaction["medications"][0].get("scheduled_time") or "").upper()
            if "PM" in prev_time or any(h in prev_time for h in ["18:", "19:", "20:", "21:", "22:"]):
                target_period = "morning"
                period_label = "morning"
                period_label_ml = "രാവിലത്തെ"
            else:
                target_period = "evening"
                period_label = "evening"
                period_label_ml = "വൈകുന്നേരത്തെ"
        else:
            target_period = "morning"

        user_str = str(user_id)
        user_meds = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
        ).all()

        matching_meds = []
        for um in user_meds:
            t = (um.reminder_time or "").upper()
            if target_period == "morning":
                if ("AM" in t and "PM" not in t) or ("PM" not in t and any(h in t for h in ["05:", "06:", "07:", "08:", "09:", "10:", "11:"])):
                    matching_meds.append(um)
            elif target_period == "evening":
                if "PM" in t or any(h in t for h in ["17:", "18:", "19:", "20:", "21:", "22:"]):
                    matching_meds.append(um)

        if not matching_meds and user_meds:
            matching_meds = [user_meds[0]]

        if matching_meds:
            med = matching_meds[0]
            dosage_str = f" ({med.dosage})" if med.dosage else ""
            time_str = med.reminder_time or "its scheduled time"
            if is_ml:
                response = f"മനസ്സിലായി, നിങ്ങളുടെ {period_label_ml} മരുന്ന്: {med.medicine_name}{dosage_str} സമയം {time_str}."
            else:
                response = f"Got it, looking at your {period_label} medicine: You have {med.medicine_name}{dosage_str} scheduled at {time_str}."
            
            med_dict = {
                "id": med.id,
                "name": med.medicine_name,
                "dosage": med.dosage or "",
                "scheduled_time": med.reminder_time or "",
                "taken": resolve_medication_daily_status(med)
            }
            return {
                "is_followup": True,
                "direct_response": response,
                "intent": "CORRECTION",
                "execution_mode": "TOOL_ONLY",
                "referenced_medications": [med_dict]
            }
        else:
            if is_ml:
                response = f"മനസ്സിലായി. നിങ്ങൾക്ക് {period_label_ml} ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകൾ ഒന്നും കാണുന്നില്ല."
            else:
                response = f"Got it. You don't have any medicines scheduled for the {period_label}."
            return {
                "is_followup": True,
                "direct_response": response,
                "intent": "CORRECTION",
                "execution_mode": "TOOL_ONLY",
                "referenced_medications": []
            }

    def _handle_explicit_entity_reference(
        self,
        low_text: str,
        referenced_meds: List[Dict[str, Any]],
        db: Session,
        is_ml: bool,
        user_id: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Handles explicit entity selection using ordinals ('the first one', 'the second one'),
        named entities ('What about Metformin?'), or time-of-day attributes ('the morning one').
        """
        target_med = None
        ref_label = ""
        ref_label_ml = ""

        # Direct Named Medicine match in candidate list
        for m in referenced_meds:
            if m.get("name") and m["name"].lower() in low_text:
                target_med = m
                ref_label = f"{m['name']} is"
                ref_label_ml = f"{m['name']}"
                break

        # Ordinal: Second
        if not target_med and any(p in low_text for p in ["second one", "the second one", "second medicine", "the other one", "other one", "രണ്ടാമത്തേത്", "രണ്ടാമത്തെ മരുന്ന്"]):
            if len(referenced_meds) >= 2:
                target_med = referenced_meds[1]
                ref_label = "The second medicine is"
                ref_label_ml = "രണ്ടാമത്തെ മരുന്ന്"
            elif referenced_meds:
                target_med = referenced_meds[0]
                ref_label = "That medicine is"
                ref_label_ml = "ആ മരുന്ന്"

        # Ordinal: First
        elif not target_med and any(p in low_text for p in ["first one", "the first one", "first medicine", "ആദ്യത്തേത്", "ആദ്യത്തെ മരുന്ന്"]):
            if referenced_meds:
                target_med = referenced_meds[0]
                ref_label = "The first medicine is"
                ref_label_ml = "ആദ്യത്തെ മരുന്ന്"

        # Attribute: Morning
        elif not target_med and any(p in low_text for p in ["morning one", "the morning one", "morning medicine", "രാവിലത്തെ മരുന്ന്", "രാവിലെ ഉള്ള"]):
            for m in referenced_meds:
                t = (m.get("scheduled_time") or "").upper()
                if ("AM" in t and "PM" not in t) or ("PM" not in t and any(h in t for h in ["05:", "06:", "07:", "08:", "09:", "10:", "11:"])):
                    target_med = m
                    ref_label = "Your morning medicine is"
                    ref_label_ml = "നിങ്ങളുടെ രാവിലത്തെ മരുന്ന്"
                    break
            if not target_med and user_id:
                user_str = str(user_id)
                all_meds = db.query(MedicineReminder).filter(
                    (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
                ).all()
                morning_meds = [m for m in all_meds if is_med_in_time_period(m, "morning")]
                if morning_meds:
                    target_med = {
                        "id": morning_meds[0].id,
                        "name": morning_meds[0].medicine_name,
                        "dosage": morning_meds[0].dosage,
                        "scheduled_time": morning_meds[0].reminder_time,
                        "taken": resolve_medication_daily_status(morning_meds[0])
                    }
                    ref_label = "Your morning medicine is"
                    ref_label_ml = "നിങ്ങളുടെ രാവിലത്തെ മരുന്ന്"

        # Attribute: Evening / Night
        elif not target_med and any(p in low_text for p in ["evening one", "the evening one", "night one", "evening medicine", "night medicine", "വൈകുന്നേരത്തെ മരുന്ന്", "രാത്രിയിലെ മരുന്ന്", "വൈകുന്നേരം"]):
            for m in referenced_meds:
                t = (m.get("scheduled_time") or "").upper()
                if "PM" in t or any(h in t for h in ["17:", "18:", "19:", "20:", "21:", "22:"]):
                    target_med = m
                    ref_label = "Your evening medicine is"
                    ref_label_ml = "നിങ്ങളുടെ വൈകുന്നേരത്തെ മരുന്ന്"
                    break
            if not target_med and user_id:
                user_str = str(user_id)
                all_meds = db.query(MedicineReminder).filter(
                    (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
                ).all()
                eve_meds = [m for m in all_meds if is_med_in_time_period(m, "evening") or is_med_in_time_period(m, "night")]
                if eve_meds:
                    target_med = {
                        "id": eve_meds[0].id,
                        "name": eve_meds[0].medicine_name,
                        "dosage": eve_meds[0].dosage,
                        "scheduled_time": eve_meds[0].reminder_time,
                        "taken": resolve_medication_daily_status(eve_meds[0])
                    }
                    ref_label = "Your evening medicine is"
                    ref_label_ml = "നിങ്ങളുടെ വൈകുന്നേരത്തെ മരുന്ന്"

        if not target_med:
            return None

        # Fetch authoritative live record from DB
        med_id = target_med.get("id")
        med_name = target_med.get("name")
        db_med = None
        if med_id:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.id == med_id).first()
        if not db_med and med_name:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.medicine_name == med_name).first()

        dosage = (db_med.dosage if db_med and db_med.dosage else target_med.get("dosage", "")).strip()
        dosage_str = f" ({dosage})" if dosage else ""
        time_str = (db_med.reminder_time if db_med and db_med.reminder_time else target_med.get("scheduled_time", "scheduled time")).strip()
        is_taken = resolve_medication_daily_status(db_med) if db_med else target_med.get("taken", False)

        # Determine user query focus for this resolved entity
        if any(p in low_text for p in ["what time", "when is", "when should i take", "when do i take", "when", "at what time", "ഏത് സമയം", "എപ്പോഴാണ്"]):
            if is_ml:
                response = f"{target_med['name']} {time_str}-നാണ് ഷെഡ്യൂൾ ചെയ്തിരിക്കുന്നത്."
            else:
                response = f"{target_med['name']} is scheduled for {time_str}."
            intent = "MEDICATION_SCHEDULE"
        elif any(p in low_text for p in ["did i take", "have i taken", "is it taken", "already taken", "കഴിച്ചോ"]):
            if is_taken:
                response = f"അതെ, നിങ്ങൾ {target_med['name']} കഴിച്ചു കഴിഞ്ഞു." if is_ml else f"Yes, you have already taken {target_med['name']}."
            else:
                response = f"ഇല്ല, നിങ്ങൾ ഇതുവരെ {target_med['name']} കഴിച്ചിട്ടില്ല. സമയം {time_str}." if is_ml else f"No, you have not taken {target_med['name']} yet. It is still scheduled for {time_str}."
            intent = "MEDICATION_STATUS"
        else:
            if is_ml:
                response = f"{ref_label_ml} {target_med['name']}{dosage_str} ആണ്, സമയം {time_str}."
            else:
                response = f"{ref_label} {target_med['name']}{dosage_str}, scheduled for {time_str}."
            intent = "MEDICATION_SCHEDULE"

        return {
            "is_followup": True,
            "direct_response": response,
            "intent": intent,
            "execution_mode": "TOOL_ONLY",
            "referenced_medications": [target_med]
        }

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
        match = re.search(r'\b(?:why\s+(?:the|is\s+there\s+a)\s+(\d+)|is\s+(?:the\s+)?(\d+)\s*(?:the\s+)?(\d+)?\s*mg|is\s+that\s+(\d+)\s*mg|does\s+(\d+)\s*mean)\b', low_text)
        contains_dosage_query = match or ("why the" in low_text and "mg" in low_text) or ("is that" in low_text and "mg" in low_text)

        if not contains_dosage_query:
            return None

        num_match = re.search(r'\b(\d+)\b', low_text)
        num_str = num_match.group(1) if num_match else "10"

        target_med = referenced_meds[0]
        med_id = target_med.get("id")
        med_name = target_med.get("name", "your medicine")

        db_med = None
        if med_id:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.id == med_id).first()
        if not db_med:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.medicine_name == med_name).first()

        actual_dosage = (db_med.dosage if db_med and db_med.dosage else "").strip()

        if actual_dosage and (f"{num_str} mg" in actual_dosage.lower() or f"{num_str}mg" in actual_dosage.lower() or actual_dosage.lower() == num_str):
            response = f"The prescribed dosage for {med_name} is {actual_dosage}."
        else:
            response = (
                f"The medicine name is '{med_name}'. I can check the prescribed dosage, "
                f"but I don't want to assume that the '{num_str}' in the medicine name means {num_str} mg. "
                "Please check your prescription or consult your doctor for the exact dosage."
            )

        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_INFORMATION",
            "execution_mode": "TOOL_ONLY",
            "referenced_medications": referenced_meds
        }

    def _is_ambiguous_reference_query(self, low_text: str) -> bool:
        """Detects if query uses a singular pronoun/reference ('that', 'that one', 'it', 'what time', 'when') when multiple items exist."""
        clean = re.sub(r"[^\w\s]", "", low_text).strip()
        if clean in ["when", "what time", "that one", "that medicine", "and that", "which one", "it", "that", "this", "എപ്പോഴാണ്", "ആ മരുന്ന്"]:
            return True
        ambiguous_signals = [
            "what time is that", "what time is it", "what time", "which one is that", "which one",
            "what medicine is that", "did i already take that one", "did i take that",
            "did i take that one", "have i taken it", "did i take it", "when is that", "when is it",
            "what about it", "what about that", "when should i take it", "when do i take it",
            "when do i take that", "when should i take this", "that medicine, when", "that medicine when",
            "when do i take the medicine", "when am i supposed to take it", "when do i have to take that",
            "when do i take", "when should i take", "at what time",
            "ആ മരുന്ന് എപ്പോഴാണ്", "അത് എപ്പോഴാണ്", "ഏത് സമയം"
        ]
        return any(p in low_text for p in ambiguous_signals)

    def _handle_tomorrow_followup(
        self,
        low_text: str,
        user_id: str,
        db: Session,
        referenced_meds: List[Dict[str, Any]],
        is_ml: bool
    ) -> Optional[Dict[str, Any]]:
        """Handles follow-ups asking about tomorrow's schedule or medicine."""
        is_tomorrow_query = any(p in low_text for p in [
            "what about tomorrow", "and tomorrow", "tomorrow?", "what do i have tomorrow", "how about tomorrow",
            "what about the next day", "and the day after", "what happens tomorrow", "tomorrow then",
            "what about the one tomorrow", "what about tomorrow's medicine",
            "is that for tomorrow", "is that tomorrow", "tomorrow", "the next day", "the day after",
            "how many do i have tomorrow", "tomorrow എന്താണ്", "നാളെയോ", "നാളത്തെ കാര്യമോ", "നാളെ എന്താണ്", "कल के बारे में क्या", "ماذا عن الغد"
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
                        "id": tm.id,
                        "name": tm.medicine_name,
                        "dosage": tm.dosage or "",
                        "scheduled_time": tt,
                        "minutes": mins if mins is not None else 9999,
                        "day": "tomorrow",
                        "taken": False
                    })
            tomorrow_meds_doses.sort(key=lambda d: d["minutes"])
            d_strs = [f"{d['name']} scheduled at {d['scheduled_time']}" for d in tomorrow_meds_doses]
            p_str = ", ".join(d_strs)
            if is_ml:
                d_strs_ml = [f"{d['name']} ({d['scheduled_time']}-ന്)" for d in tomorrow_meds_doses]
                response = f"നാളെ നിങ്ങൾക്ക് {', '.join(d_strs_ml)} ആണ് ഉള്ളത്."
            else:
                response = f"Tomorrow you have {p_str}."
        else:
            tomorrow_meds_doses = []
            response = "നാളെ നിങ്ങൾക്ക് ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകൾ ഒന്നും ഇല്ല." if is_ml else "You have no medicines scheduled for tomorrow."

        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_SCHEDULE",
            "execution_mode": "TOOL_ONLY",
            "referenced_medications": tomorrow_meds_doses if tomorrow_meds_doses else referenced_meds
        }

    def _handle_identity_followup(
        self,
        low_text: str,
        referenced_meds: List[Dict[str, Any]],
        is_ml: bool
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
        response = f"ആ മരുന്ന് {med['name']} ആണ്." if is_ml else f"That medicine is {med['name']}."
        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_INFORMATION",
            "execution_mode": "TOOL_ONLY",
            "referenced_medications": referenced_meds
        }

    def _handle_time_followup(
        self,
        low_text: str,
        referenced_meds: List[Dict[str, Any]],
        is_ml: bool
    ) -> Optional[Dict[str, Any]]:
        """Handles questions asking for the scheduled time of the referenced medicine ('What time?')."""
        clean = re.sub(r"[^\w\s]", "", low_text).strip()
        is_time_query = any(p in low_text for p in [
            "what time", "what time is that", "what time is it", "when is that",
            "when is it", "at what time", "when should i take", "when do i take",
            "when am i supposed to take", "when do i have to take", "that medicine, when", "that medicine when",
            "what time do i take", "that medicine", "and that one", "and that",
            "that medicine എപ്പോഴാ", "my medicine എപ്പോഴാണ്", "അത് എപ്പോഴാണ്",
            "ഏത് സമയം", "എപ്പോഴാണ്", "किस समय", "في أي وقت"
        ]) or clean in ["when", "what time", "and that one", "and that", "that one", "that medicine"]
        if not is_time_query:
            return None

        med = referenced_meds[0]
        day_str = f" {med.get('day', 'tomorrow')}" if med.get("day") else ""
        time_str = med.get("scheduled_time") or "its scheduled time"
        if is_ml:
            response = f"{med['name']} {time_str}-നാണ് ഷെഡ്യൂൾ ചെയ്തിരിക്കുന്നത്."
        else:
            response = f"{med['name']} is scheduled for {time_str}{day_str}."
        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_SCHEDULE",
            "execution_mode": "TOOL_ONLY",
            "referenced_medications": referenced_meds
        }

    def _handle_taken_confirmation(
        self,
        low_text: str,
        user_id: str,
        db: Session,
        referenced_meds: List[Dict[str, Any]],
        is_ml: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Understands statements confirming the user took a medicine ('I already took that medicine', 'ഞാൻ അത് കഴിച്ചു').
        Authoritatively marks today's occurrence as taken via medicine_service.mark_taken, verifies live DB status,
        and provides natural feedback while preserving historical records and preventing future recurring alterations.
        """
        # 1. Safety check: ensure utterance is NOT a question or inquiry or clarification
        is_question = any(q in low_text for q in [
            "did i", "have i", "was it", "is it", "when", "what", "can i", "should i", 
            "കഴിച്ചോ", "കഴിഞ്ഞോ", "എടുത്തോ", "ആണോ", "ഉണ്ടോ", "சாப்பிட்டீர்களா", "எடுத்தீர்களா",
            "क्या मैंने", "कब", "?"
        ])
        if is_question:
            return None

        # 2. Taken confirmation intent patterns
        taken_patterns = [
            r"\bi already took that medicine\b",
            r"\bi already took that\b",
            r"\bi already took it\b",
            r"\bi already took\b",
            r"\bi took that medicine\b",
            r"\bi took that\b",
            r"\bi took it already\b",
            r"\bi took it\b",
            r"\bi took\b",
            r"\bi have already taken\b",
            r"\bi've already taken\b",
            r"\bi have taken\b",
            r"\bi've taken\b",
            r"\byes,? i already took that\b",
            r"\byes,? i took it\b",
            r"\byes,? already took it\b",
            r"\balready took that medicine\b",
            r"\balready took that\b",
            r"\balready took it\b",
            r"\balready took\b",
            r"\balready taken\b",
            r"\bmark it as taken\b",
            r"\bmark as taken\b",
            r"\bmark it taken\b",
            r"\byes,? mark it taken\b",
            r"\bokay,? i took it\b",
            r"\bok,? i took it\b",
            r"\bi have taken it\b",
            r"\bi have already taken it\b",
            r"\bi have taken that\b",
            r"\bi've taken it\b",
            r"\bi've already taken it\b",
            r"\bi took my medicine\b",
            r"\bi already took my medicine\b",
            r"\bjust took it\b",
            r"\bjust took that\b",
            r"\bjust took my medicine\b",
            r"\bjust took\b",
            r"\bdone\b",
            # Malayalam script
            r"ഞാൻ അത് കഴിച്ചു",
            r"അത് ഞാൻ കഴിച്ചു",
            r"മരുന്ന് കഴിച്ചു",
            r"ഞാൻ മരുന്ന് കഴിച്ചു",
            r"ഞാൻ മരുന്ന് എടുത്തു",
            r"അതെടുത്തിട്ടുണ്ട്",
            r"ഞാൻ കഴിച്ചു",
            r"കഴിച്ചു കഴിഞ്ഞു",
            r"കഴിച്ചു",
            r"എടുത്തു",
            r"കഴിച്ചിട്ടുണ്ട്",
            r"അതെടുത്തു",
            # Tamil script
            r"சாப்பிட்டேன்",
            r"மருந்து சாப்பிட்டேன்",
            r"நான் சாப்பிட்டேன்",
            r"எடுத்துக்கொண்டேன்",
            # Hindi script
            r"मैंने दवा ले ली",
            r"मैंने वह दवा ले ली",
            r"दवा ले ली",
            r"ले ली है",
            r"खा ली है",
            r"दवा खा ली",
            # Manglish / Romanized Malayalam
            r"\bnjan athu kazhichu\b",
            r"\bathu njan kazhichu\b",
            r"\bmarunnu kazhichu\b",
            r"\bnjan marunnu kazhichu\b",
            r"\bnjan kazhichu\b",
            r"\bnjan eduthu\b",
            r"\bkazhichu kazhinju\b",
            r"\bkazhichittundu\b",
            r"\bkazhichu\b"
        ]

        is_taken_intent = any(re.search(p, low_text, re.I) for p in taken_patterns)
        if not is_taken_intent:
            return None

        user_str = str(user_id)
        user_meds = db.query(MedicineReminder).filter(
            (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
        ).all()

        # 3. Resolve Target Medicine
        target_med = None

        # Check if user mentioned an explicit medicine name in low_text
        for um in user_meds:
            if um.medicine_name and len(um.medicine_name) > 2 and um.medicine_name.lower() in low_text:
                target_med = {
                    "id": um.id,
                    "name": um.medicine_name,
                    "dosage": um.dosage or "",
                    "scheduled_time": um.reminder_time or "",
                    "day": "today"
                }
                break

        # If not explicit, resolve from referenced_meds
        if not target_med:
            if len(referenced_meds) == 1:
                target_med = referenced_meds[0]
            elif len(referenced_meds) > 1:
                # Ambiguous reference among multiple medicines -> ask concise clarification
                med_a = referenced_meds[0]
                med_b = referenced_meds[1]
                time_a = med_a.get("scheduled_time") or "scheduled time"
                time_b = med_b.get("scheduled_time") or "scheduled time"
                if is_ml:
                    clarification = f"നിങ്ങൾ {med_a['name']} ({time_a}) ആണോ {med_b['name']} ({time_b}) ആണോ കഴിച്ചത്?"
                else:
                    clarification = f"Do you mean you took {med_a['name']} at {time_a} or {med_b['name']} at {time_b}?"
                return {
                    "is_followup": True,
                    "direct_response": clarification,
                    "intent": "Clarification",
                    "execution_mode": "CLARIFICATION",
                    "referenced_medications": referenced_meds
                }
            else:
                # referenced_meds is empty: inspect user's schedule for today
                user_obj = db.query(User).filter(User.id == user_str).first()
                tz_name = (user_obj.timezone if user_obj and user_obj.timezone else "UTC").strip()
                try:
                    user_tz = pytz.timezone(tz_name)
                except Exception:
                    user_tz = pytz.utc
                now_local = datetime.datetime.now(user_tz)
                local_today = now_local.date()

                today_meds = [m for m in user_meds if med_applies_on_date(m, local_today)]
                today_pending = [m for m in today_meds if not resolve_medication_daily_status(m, target_date=local_today, tz_name=tz_name)]

                if len(today_pending) == 1:
                    um = today_pending[0]
                    target_med = {
                        "id": um.id,
                        "name": um.medicine_name,
                        "dosage": um.dosage or "",
                        "scheduled_time": um.reminder_time or "",
                        "day": "today"
                    }
                elif len(today_pending) > 1:
                    med_names = ", ".join(m.medicine_name for m in today_pending[:3])
                    if is_ml:
                        msg = f"ഏത് മരുന്നാണ് കഴിച്ചത്? ഇന്ന് {med_names} ഷെഡ്യൂൾ ചെയ്തിട്ടുണ്ട്."
                    else:
                        msg = f"Which medicine did you take? You have {med_names} scheduled for today."
                    return {
                        "is_followup": True,
                        "direct_response": msg,
                        "intent": "Clarification",
                        "execution_mode": "CLARIFICATION",
                        "referenced_medications": [{"id": m.id, "name": m.medicine_name, "scheduled_time": m.reminder_time} for m in today_pending]
                    }
                elif today_meds:
                    # All today's medicines already taken
                    first_m = today_meds[0]
                    target_med = {
                        "id": first_m.id,
                        "name": first_m.medicine_name,
                        "dosage": first_m.dosage or "",
                        "scheduled_time": first_m.reminder_time or "",
                        "day": "today"
                    }
                else:
                    no_med_msg = "നിങ്ങൾക്ക് ഇന്ന് ഷെഡ്യൂൾ ചെയ്ത മരുന്നുകളൊന്നും റെക്കോർഡിൽ ഇല്ല." if is_ml else "You have no medicines scheduled in your records for today."
                    return {
                        "is_followup": True,
                        "direct_response": no_med_msg,
                        "intent": "MEDICATION_STATUS",
                        "execution_mode": "TOOL_ONLY"
                    }

        if not target_med:
            return None

        med_id = target_med.get("id")
        med_name = target_med.get("name", "your medicine")

        # 4. Check if target medicine is scheduled for tomorrow
        if target_med.get("day") == "tomorrow":
            time_str = target_med.get("scheduled_time", "")
            if is_ml:
                reply = f"{med_name} നാളെ {time_str}-നാണ് ഷെഡ്യൂൾ ചെയ്തിരിക്കുന്നത്. ഇന്നത്തെ ഷെഡ്യൂളിൽ ഇല്ല."
            else:
                reply = f"{med_name} is scheduled for tomorrow at {time_str}. It is not scheduled for today."
            return {
                "is_followup": True,
                "direct_response": reply,
                "intent": "MEDICATION_SCHEDULE",
                "execution_mode": "TOOL_ONLY",
                "referenced_medications": [target_med]
            }

        # 5. Retrieve authoritative DB record
        db_med = None
        if med_id:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.id == med_id).first()
        if not db_med:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.medicine_name == med_name).first()

        if not db_med:
            err_reply = f"ക്ഷമിക്കണം, {med_name} സിസ്റ്റത്തിൽ കണ്ടെത്താനായില്ല." if is_ml else f"I couldn't find a record for {med_name}."
            return {
                "is_followup": True,
                "direct_response": err_reply,
                "intent": "MEDICATION_STATUS",
                "execution_mode": "TOOL_ONLY"
            }

        # 6. Check if already taken today
        is_already_taken = resolve_medication_daily_status(db_med)
        if is_already_taken:
            already_reply = f"{med_name} ഇന്ന് നേരത്തെ തന്നെ കഴിച്ചതായി രേഖപ്പെടുത്തിയിട്ടുണ്ട്." if is_ml else f"{med_name} is already marked as taken for today."
            return {
                "is_followup": True,
                "direct_response": already_reply,
                "intent": "MEDICATION_STATUS",
                "execution_mode": "TOOL_ONLY",
                "referenced_medications": [{
                    "id": db_med.id,
                    "name": db_med.medicine_name,
                    "dosage": db_med.dosage or "",
                    "scheduled_time": db_med.reminder_time or "",
                    "taken": True
                }]
            }

        # 7. Call authoritative mark_taken mechanism
        from services.medicine_service import mark_taken
        updated = mark_taken(db, reminder_id=db_med.id, subject_id=user_str)

        # 8. Authoritative Verification
        db.refresh(db_med)
        is_verified = resolve_medication_daily_status(db_med)

        if is_verified:
            if is_ml:
                success_reply = f"ശരി. {db_med.medicine_name} ഇന്ന് കഴിച്ചതായി ഞാൻ രേഖപ്പെടുത്തിയിട്ടുണ്ട്."
            else:
                success_reply = f"Got it. I've marked {db_med.medicine_name} as taken for today."

            # Update interaction context with authoritative status
            conversation_manager.save_interaction_context(user_id, {
                "intent": "MEDICATION_STATUS",
                "tool": "mark_taken",
                "medications": [{
                    "id": db_med.id,
                    "name": db_med.medicine_name,
                    "dosage": db_med.dosage or "",
                    "scheduled_time": db_med.reminder_time or "",
                    "taken": True
                }],
                "response_text": success_reply
            })

            # Broadcast real-time update to websocket stream if loop is active
            try:
                from services.websocket_manager import manager
                import asyncio
                payload = {
                    "type": "medicine_taken",
                    "medicine_id": db_med.id,
                    "medicine_name": db_med.medicine_name,
                    "message": f"Medicine {db_med.medicine_name} was marked as taken."
                }
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(manager.send_personal_message(payload, user_str))
            except Exception:
                pass

            return {
                "is_followup": True,
                "direct_response": success_reply,
                "intent": "MEDICATION_STATUS",
                "execution_mode": "TOOL_ONLY",
                "referenced_medications": [{
                    "id": db_med.id,
                    "name": db_med.medicine_name,
                    "dosage": db_med.dosage or "",
                    "scheduled_time": db_med.reminder_time or "",
                    "taken": True
                }]
            }
        else:
            fail_reply = f"ക്ഷമിക്കണം, {db_med.medicine_name} കഴിച്ചതായി രേഖപ്പെടുത്താൻ കഴിഞ്ഞില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക." if is_ml else f"I was unable to update the status for {db_med.medicine_name}. Please try again."
            return {
                "is_followup": True,
                "direct_response": fail_reply,
                "intent": "MEDICATION_STATUS",
                "execution_mode": "TOOL_ONLY"
            }

    def _handle_status_followup(
        self,
        low_text: str,
        referenced_meds: List[Dict[str, Any]],
        db: Session,
        is_ml: bool,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Handles questions asking whether a medicine was taken ('Did I already take that one?', 'Did I take it?')."""
        status_patterns = [
            r"\bdid i already take that one\b",
            r"\bdid i already take that\b",
            r"\bdid i already take it\b",
            r"\bdid i take that one\b",
            r"\bdid i take that medicine\b",
            r"\bdid i take that\b",
            r"\bdid i take it already\b",
            r"\bdid i take it\b",
            r"\bdid i take my medicine\b",
            r"\bdid i take the medicine\b",
            r"\bhave i taken that one\b",
            r"\bhave i taken that medicine\b",
            r"\bhave i taken that\b",
            r"\bhave i taken it already\b",
            r"\bhave i taken it yet\b",
            r"\bhave i taken it\b",
            r"\bhave i taken my medicine\b",
            r"\bis it marked as taken\b",
            r"\bis that marked as taken\b",
            r"\bis it taken\b",
            r"\bis that taken\b",
            r"\bwas that taken\b",
            r"\bwas it taken\b",
            r"\bmarked as taken\b",
            # Malayalam
            r"ഞാൻ അത് കഴിച്ചോ",
            r"അത് കഴിച്ചോ",
            r"മരുന്ന് കഴിച്ചോ",
            r"ഞാൻ മരുന്ന് കഴിച്ചോ",
            r"എന്റെ മരുന്ന് കഴിച്ചോ",
            r"കഴിച്ചോ",
            r"കഴിഞ്ഞോ",
            # Manglish
            r"\bnjan athu kazhicho\b",
            r"\bathu kazhicho\b",
            r"\bmarunnu kazhicho\b",
            r"\bkazhicho\b",
            r"\bkazhinjo\b",
            # Other languages
            r"क्या मैंने वह ले ली",
            r"هل أخذت ذلك الدواء"
        ]

        is_status_query = any(re.search(p, low_text, re.I) for p in status_patterns)
        if not is_status_query:
            return None

        # Resolve target medicine:
        # 1. Check if an explicit medicine name is mentioned in query
        user_str = str(user_id) if user_id else ""
        user_meds = []
        if user_str:
            user_meds = db.query(MedicineReminder).filter(
                (MedicineReminder.elder_id == user_str) | (MedicineReminder.subject_id == user_str)
            ).all()

        target_med = None
        for um in user_meds:
            if um.medicine_name and len(um.medicine_name) > 2 and um.medicine_name.lower() in low_text:
                target_med = {
                    "id": um.id,
                    "name": um.medicine_name,
                    "dosage": um.dosage or "",
                    "scheduled_time": um.reminder_time or "",
                    "day": "today"
                }
                break

        if not target_med:
            if len(referenced_meds) == 1:
                target_med = referenced_meds[0]
            elif len(referenced_meds) > 1:
                # Ambiguous: ask concise clarification
                med_a = referenced_meds[0]
                med_b = referenced_meds[1]
                time_a = med_a.get("scheduled_time") or "scheduled time"
                time_b = med_b.get("scheduled_time") or "scheduled time"
                if is_ml:
                    clarification = f"നിങ്ങൾ {med_a['name']} ({time_a}) ആണോ {med_b['name']} ({time_b}) ആണോ ചോദിക്കുന്നത്?"
                else:
                    clarification = f"Do you mean {med_a['name']} at {time_a} or {med_b['name']} at {time_b}?"
                return {
                    "is_followup": True,
                    "direct_response": clarification,
                    "intent": "Clarification",
                    "execution_mode": "CLARIFICATION",
                    "referenced_medications": referenced_meds
                }
            elif user_meds:
                # Look at today's medicines
                user_obj = db.query(User).filter(User.id == user_str).first()
                tz_name = (user_obj.timezone if user_obj and user_obj.timezone else "UTC").strip()
                try:
                    user_tz = pytz.timezone(tz_name)
                except Exception:
                    user_tz = pytz.utc
                now_local = datetime.datetime.now(user_tz)
                local_today = now_local.date()

                today_meds = [m for m in user_meds if med_applies_on_date(m, local_today)]
                if len(today_meds) == 1:
                    um = today_meds[0]
                    target_med = {
                        "id": um.id,
                        "name": um.medicine_name,
                        "dosage": um.dosage or "",
                        "scheduled_time": um.reminder_time or "",
                        "day": "today"
                    }
                elif len(today_meds) > 1:
                    # Check pending first, else earliest
                    pending = [m for m in today_meds if not resolve_medication_daily_status(m, target_date=local_today, tz_name=tz_name)]
                    if len(pending) == 1:
                        um = pending[0]
                        target_med = {
                            "id": um.id,
                            "name": um.medicine_name,
                            "dosage": um.dosage or "",
                            "scheduled_time": um.reminder_time or "",
                            "day": "today"
                        }
                    else:
                        med_names = ", ".join(m.medicine_name for m in today_meds[:3])
                        if is_ml:
                            msg = f"ഏത് മരുന്നിനെക്കുറിച്ചാണ് ചോദിക്കുന്നത്? ഇന്ന് {med_names} ഉണ്ട്."
                        else:
                            msg = f"Which medicine are you asking about? You have {med_names} scheduled for today."
                        return {
                            "is_followup": True,
                            "direct_response": msg,
                            "intent": "Clarification",
                            "execution_mode": "CLARIFICATION",
                            "referenced_medications": [{"id": m.id, "name": m.medicine_name, "scheduled_time": m.reminder_time} for m in today_meds]
                        }

        if not target_med:
            not_found_msg = "നിങ്ങളുടെ റെക്കോർഡുകളിൽ മരുന്നുകളൊന്നും കണ്ടെത്തിയില്ല." if is_ml else "You have no medicine scheduled under that name."
            return {
                "is_followup": True,
                "direct_response": not_found_msg,
                "intent": "MEDICATION_STATUS",
                "execution_mode": "TOOL_ONLY"
            }

        med_id = target_med.get("id")
        med_name = target_med.get("name", "that medicine")

        db_med = None
        if med_id:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.id == med_id).first()
        if not db_med:
            db_med = db.query(MedicineReminder).filter(MedicineReminder.medicine_name == med_name).first()

        if target_med.get("day") == "tomorrow":
            is_taken = False
        else:
            is_taken = resolve_medication_daily_status(db_med) if db_med else target_med.get("taken", False)

        time_str = (db_med.reminder_time if db_med and db_med.reminder_time else target_med.get("scheduled_time", "scheduled time")).strip()

        if is_taken:
            response = f"അതെ, നിങ്ങൾ {med_name} കഴിച്ചു കഴിഞ്ഞു. ഇന്ന് കഴിച്ചതായി രേഖപ്പെടുത്തിയിട്ടുണ്ട്." if is_ml else f"Yes, you have already taken {med_name}. It is marked as taken for today."
        else:
            if is_ml:
                response = f"ഇല്ല, നിങ്ങൾ ഇതുവരെ {med_name} കഴിച്ചിട്ടില്ല. സമയം {time_str}."
            else:
                response = f"No, you have not taken {med_name} yet. You haven't marked it as taken for today. It is scheduled for {time_str}."

        return {
            "is_followup": True,
            "direct_response": response,
            "intent": "MEDICATION_STATUS",
            "execution_mode": "TOOL_ONLY",
            "referenced_medications": [target_med]
        }

conversational_reference_resolver = ConversationalReferenceResolver()
