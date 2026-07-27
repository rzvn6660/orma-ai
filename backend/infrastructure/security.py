class SecurityService:
    def rate_limit(self, user_id: str) -> bool:
        return True
        
    def mask_phi(self, data: str) -> str:
        if "patient" in data.lower():
            return "MASKED_DATA"
        return data
