from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from .models import Role

def role_required(allowed_roles):
    """
    Decorator to enforce that the authenticated user possesses one of the allowed roles.
    Rejects unauthorized requests server-side with HTTP 403 Forbidden.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Superuser always has full authority
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            user_role = getattr(request.user, 'role', None)
            if user_role not in allowed_roles:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'error': f'Permission denied. Required role: {", ".join(allowed_roles)}. Your role is: {user_role}.'
                    }, status=403)
                raise PermissionDenied(f"Permission denied: Access requires one of [{', '.join(allowed_roles)}].")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def authority_required(view_func):
    """Restricts view execution strictly to users with the Authority role."""
    return role_required([Role.AUTHORITY])(view_func)

def lead_or_authority_required(view_func):
    """Restricts view execution strictly to Leads and Authorities (e.g., Task assignment, Meeting creation)."""
    return role_required([Role.AUTHORITY, Role.LEAD])(view_func)
