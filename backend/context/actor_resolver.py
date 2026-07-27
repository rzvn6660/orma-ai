from models.user import User

class ActorResolver:
    @staticmethod
    def resolve(user: User):
        """
        The actor is always the authenticated user making the request.
        """
        return {
            "id": user.id,
            "name": getattr(user, "name", "User"),
            "role": getattr(user, "role", "elderly")
        }
