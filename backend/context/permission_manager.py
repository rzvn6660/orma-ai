from typing import List

class PermissionManager:
    ROLE_PERMISSIONS = {
        "caregiver": [
            "add_medicine",
            "edit_medicine",
            "add_appointment",
            "add_health_record",
            "view_reports",
            "view_reminders",
            "manage_elderly"
        ],
        "doctor": [
            "view_patient",
            "add_consultation_notes",
            "upload_reports",
            "view_medications"
        ],
        "elderly": [
            "manage_own_health"
        ]
    }

    @classmethod
    def get_permissions(cls, role: str) -> List[str]:
        return cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def has_permission(cls, role: str, permission: str) -> bool:
        return permission in cls.get_permissions(role)

    @classmethod
    def can(cls, role: str, action: str) -> bool:
        return cls.has_permission(role, action)

    @classmethod
    def canRead(cls, role: str, resource: str) -> bool:
        return cls.has_permission(role, f"read_{resource}")

    @classmethod
    def canWrite(cls, role: str, resource: str) -> bool:
        return cls.has_permission(role, f"write_{resource}")

    @classmethod
    def canShare(cls, role: str, resource: str) -> bool:
        return cls.has_permission(role, f"share_{resource}")

    @classmethod
    def canDelete(cls, role: str, resource: str) -> bool:
        return cls.has_permission(role, f"delete_{resource}")

    @classmethod
    def canManage(cls, role: str, resource: str) -> bool:
        return cls.has_permission(role, f"manage_{resource}")
