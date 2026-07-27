from models.user import User

class RoleManager:
    @staticmethod
    def get_role(user: User) -> str:
        if hasattr(user, "role") and user.role:
            return user.role
        return "elderly"
