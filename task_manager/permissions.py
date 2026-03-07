from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    # Shown when someone tries to access a task that isn't theirs
    message = "You don't have permission to access this — it belongs to another user."

    def has_permission(self, request, view):
        # Basic check are they logged in at all?
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Make sure the task's user matches whoever is making the request
        return obj.user == request.user


class IsSelfOrAdmin(BasePermission):
    message = "You can only manage your own account."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admins can access any account regular users can only access their own
        return obj == request.user or request.user.is_staff
