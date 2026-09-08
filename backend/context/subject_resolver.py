import re
from models.user import User

# Sentinel value used when a caregiver has no approved linked patient.
# Any code path that receives this must treat it as "no subject" and
# respond with an appropriate error — never invent a patient ID.
NO_LINKED_PATIENT_SENTINEL = "__no_linked_patient__"

class SubjectResolver:
    @staticmethod
    def resolve(actor: dict, text: str, db_session=None, active_subject_id: str = None):
        """
        Determines the subject of the conversation based on the actor and the text.
        Also flags if clarification is needed.

        For caregivers with zero approved linked patients, returns subject_id=NO_LINKED_PATIENT_SENTINEL
        rather than falling back to a hardcoded placeholder like "default_elderly" or "John".
        """
        # Default subject is the actor themselves
        subject_id = actor["id"]
        subject_name = actor["name"]
        subject_role = actor["role"]
        requires_clarification = False
        clarification_message = None

        text_lower = text.lower()
        first_person_pronouns = [" i ", " me ", " my ", " mine ", "^i ", "^my "]

        has_first_person = any(re.search(p, f" {text_lower} ") for p in first_person_pronouns)

        if actor["role"] == "caregiver":
            # If the UI specifically sent the active subject ID, use it directly.
            if active_subject_id and db_session:
                patient = db_session.query(User).filter(User.id == str(active_subject_id)).first()
                if not patient and str(active_subject_id).isdigit():
                    patient = db_session.query(User).filter(User.id == int(active_subject_id)).first()
                if patient:
                    return {
                        "id": str(patient.id),
                        "name": patient.name,
                        "role": patient.role,
                        "requires_clarification": False,
                        "clarification_message": None
                    }

            # Resolve from database relationships if available.
            linked_patient_id = NO_LINKED_PATIENT_SENTINEL
            linked_patient_name = None

            if db_session:
                from models.user import CaregiverRelationship
                rels = db_session.query(CaregiverRelationship).filter(
                    CaregiverRelationship.caregiver_id == str(actor["id"]),
                    CaregiverRelationship.status == "approved"
                ).all()
                if len(rels) == 1:
                    patient = db_session.query(User).filter(User.id == rels[0].elder_id).first()
                    if patient:
                        linked_patient_id = str(patient.id)
                        linked_patient_name = patient.name
                elif len(rels) > 1:
                    # Multiple approved patients — requires explicit subject selection via header.
                    # Without a header, we cannot guess which patient is intended.
                    linked_patient_id = NO_LINKED_PATIENT_SENTINEL
                    linked_patient_name = None

            if has_first_person:
                # Ambiguous: is it caregiver's own medicine, or the patient's?
                requires_clarification = True
                clarification_message = "Are you referring to your own health or your patient's?"
            else:
                subject_id = linked_patient_id
                subject_name = linked_patient_name or ""
                subject_role = "elderly"

        elif actor["role"] == "doctor":
            # Doctor must specify patient
            if "john" in text_lower:
                requires_clarification = True
                clarification_message = "Which patient are you referring to?"
            elif has_first_person and " my " in text_lower:
                subject_id = actor["id"]
                subject_name = actor["name"]
            else:
                requires_clarification = True
                clarification_message = "Which patient are you referring to?"

        return {
            "id": subject_id,
            "name": subject_name,
            "role": subject_role,
            "requires_clarification": requires_clarification,
            "clarification_message": clarification_message
        }
