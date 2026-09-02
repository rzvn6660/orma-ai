import re
from models.user import User

class SubjectResolver:
    @staticmethod
    def resolve(actor: dict, text: str, db_session=None, active_subject_id: str = None):
        """
        Determines the subject of the conversation based on the actor and the text.
        Also flags if clarification is needed.
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
            # If the UI specifically sent the active subject ID, use it directly
            if active_subject_id and db_session:
                patient = db_session.query(User).filter(User.id == str(active_subject_id)).first()
                if not patient and str(active_subject_id).isdigit():
                    patient = db_session.query(User).filter(User.id == int(active_subject_id)).first()
                if patient:
                    subject_id = str(patient.id)
                    subject_name = patient.name
                    subject_role = patient.role
                    return {
                        "id": subject_id,
                        "name": subject_name,
                        "role": subject_role,
                        "requires_clarification": False,
                        "clarification_message": None
                    }
                    
            # Resolve from database relationships if available
            linked_patient_name = "John"
            linked_patient_id = "default_elderly"
            
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
            
            if has_first_person:
                # Ambiguous: is it caregiver's own medicine, or the patient's?
                requires_clarification = True
                clarification_message = f"Are you referring to your own health or your patient's?"
            else:
                subject_id = linked_patient_id
                subject_name = linked_patient_name
                subject_role = "elderly"
                    
        elif actor["role"] == "doctor":
            # Doctor must specify patient
            if "john" in text_lower:
                subject_id = "default_elderly"
                subject_name = "John"
                subject_role = "elderly"
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
