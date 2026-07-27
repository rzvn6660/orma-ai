from typing import List
from .doctor_models import PatientSnapshot, RiskSummary

class QuestionGenerator:
    def generate_questions(self, snapshot: PatientSnapshot, risks: RiskSummary) -> List[str]:
        questions = []
        
        if snapshot.missed_medications:
            questions.append("What should I do if I keep missing my medication doses?")
            
        if snapshot.recent_symptoms:
            questions.append(f"Are my recent symptoms ({', '.join(snapshot.recent_symptoms[:2])}) something to worry about?")
            
        for risk in risks.high_risks:
            if "Blood Pressure" in risk:
                questions.append("Why is my blood pressure abnormal and what can we do?")
            if "Sugar" in risk:
                questions.append("Is my blood sugar trend indicating a change in my condition?")
                
        if len(snapshot.current_medications) > 2:
            questions.append("Can any of my current medications be reduced or stopped?")
            
        if not questions:
            questions.append("Based on my recent health logs, is there anything I should change in my daily routine?")
            
        return questions
