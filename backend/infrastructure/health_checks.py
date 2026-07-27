class HealthCheckService:
    def check_provider(self) -> bool:
        return True
        
    def check_database(self) -> bool:
        return True
        
    def get_system_status(self) -> dict:
        return {
            "status": "healthy",
            "provider": self.check_provider(),
            "database": self.check_database()
        }
