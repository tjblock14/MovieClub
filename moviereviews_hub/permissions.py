from rest_framework import permissions

class IsReviewOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission: allow safe methods for everyone,
    but only the review's owner can edit or delete it.
    """

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS = GET, HEAD, OPTIONS — everyone can view
        if request.method in permissions.SAFE_METHODS:
            return True
        # Otherwise, only allow the review's owner to edit/delete
        return obj.user == request.user
