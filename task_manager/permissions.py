"""
permissions.py — Custom Permission Classes

Controls WHO can do WHAT.
Return True = allow, False = deny (403 Forbidden).
"""

from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Only the user who created a task can access it.
    Prevents users from reading or editing each other's tasks.
    """

    message = "You do not have permission to access this resource."

    def has_permission(self, request, view):
        """View-level: is the user logged in at all?"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level: does this user own this specific task?
        obj.user is the FK to the User who created the task.
        """
        return obj.user == request.user


class IsSelfOrAdmin(BasePermission):
    """
    For User endpoints: users can only manage their own account,
    unless they are an admin.
    """

    message = "You can only manage your own account."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """obj here is a User instance."""
        return obj == request.user or request.user.is_staff
