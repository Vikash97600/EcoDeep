from rest_framework import permissions

from apps.users.models import RoleChoices


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """Custom permission allowing read-only access for anyone, but write access only to Admins."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role.role_name == RoleChoices.ADMIN


class IsResearcherOrAdmin(permissions.BasePermission):
    """Custom permission allowing access to Researchers and Administrators."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and hasattr(request.user, 'profile')):
            return False
        return request.user.profile.role.role_name in [RoleChoices.ADMIN, RoleChoices.RESEARCHER]
