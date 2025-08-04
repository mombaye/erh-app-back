from rest_framework import permissions

class IsStaffOrGlobalAdmin(permissions.BasePermission):
    """
    Permission pour permettre uniquement aux users staff OU global admin.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and
            (user.is_staff or getattr(user, "is_global_admin", False))
        )
