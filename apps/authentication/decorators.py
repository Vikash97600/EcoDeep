from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles=[]):
    """Decorator restricting view execution to specific user roles."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect('authentication:login')
            
            # Superusers and staff always have permission
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)
            
            user_profile = getattr(request.user, 'profile', None)
            if user_profile and user_profile.role:
                if user_profile.role.role_name in allowed_roles:
                    return view_func(request, *args, **kwargs)
            else:
                # Allow authenticated users without explicit role restriction
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "Access Denied: You do not possess permission to perform this action.")
            raise PermissionDenied
        return _wrapped_view
    return decorator

# Role Decorator Wrappers
admin_required = role_required(['ADMIN'])
researcher_required = role_required(['ADMIN', 'RESEARCHER'])
developer_required = role_required(['ADMIN', 'RESEARCHER', 'DEVELOPER'])
