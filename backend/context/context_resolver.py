from models.user import User
from .actor_resolver import ActorResolver
from .subject_resolver import SubjectResolver
from .permission_manager import PermissionManager
from .conversation_context import ConversationContext

class ContextResolver:
    @staticmethod
    def resolve(user: User, text: str, db_session=None, active_subject_id: str = None) -> ConversationContext:
        # 1. Resolve Actor
        actor_data = ActorResolver.resolve(user)
        
        # 2. Resolve Subject (and check for clarification)
        subject_data = SubjectResolver.resolve(actor_data, text, db_session, active_subject_id)
        
        # 3. Resolve Permissions based on Actor's role
        permissions = PermissionManager.get_permissions(actor_data["role"])
        
        # 4. Construct Context
        return ConversationContext(
            actor_id=actor_data["id"],
            actor_name=actor_data["name"],
            actor_role=actor_data["role"],
            subject_id=subject_data["id"],
            subject_name=subject_data["name"],
            subject_role=subject_data["role"],
            permissions=permissions,
            requires_clarification=subject_data["requires_clarification"],
            clarification_message=subject_data["clarification_message"]
        )
