from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class MedicalSourceProvider(ABC):
    """Base interface for medical knowledge providers (e.g., OpenFDA, NHS, Vector DB)."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def retrieve_drug_info(self, drug_name: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def retrieve_condition_info(self, condition_name: str) -> Optional[Dict[str, Any]]:
        pass

class MockMedicalProvider(MedicalSourceProvider):
    """A simple mock provider to stand in for a real API or Vector DB."""
    
    @property
    def provider_name(self) -> str:
        return "mock_medical_provider"

    def retrieve_drug_info(self, drug_name: str) -> Optional[Dict[str, Any]]:
        # Hardcoded mock knowledge
        drug_db = {
            "aspirin": {
                "description": "Aspirin is used to reduce fever and relieve mild to moderate pain.",
                "side_effects": ["upset stomach", "heartburn"],
                "interactions": ["blood thinners", "ibuprofen"]
            }
        }
        return drug_db.get(drug_name.lower())

    def retrieve_condition_info(self, condition_name: str) -> Optional[Dict[str, Any]]:
        condition_db = {
            "hypertension": {
                "description": "High blood pressure is a common condition in which the long-term force of the blood against your artery walls is high enough that it may eventually cause health problems.",
                "guidance": "Regular monitoring, low sodium diet, and prescribed medications."
            }
        }
        return condition_db.get(condition_name.lower())
