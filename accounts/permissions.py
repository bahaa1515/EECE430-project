from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def coach_required(view_func):
    """Allows access to coaches AND managers (both are staff roles)."""
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff_role():
            raise PermissionDenied("Coach or Manager access is required for this action.")
        return view_func(request, *args, **kwargs)
    return _wrapped


def manager_required(view_func):
    """Allows access to managers only."""
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_manager():
            raise PermissionDenied("Manager access is required for this action.")
        return view_func(request, *args, **kwargs)
    return _wrapped
