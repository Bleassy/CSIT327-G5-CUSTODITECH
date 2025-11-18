from django.shortcuts import redirect
from django.contrib import messages

def student_required(function):
    """
    Decorator to ensure a user is logged in and is a 'student'.
    
    Wraps a view function to enforce student-only access. Checks if the user is authenticated
    and verifies their user_type is 'student'. Redirects unauthenticated users to the login page
    and non-student users (such as admins) to the admin dashboard with appropriate warning messages.
    Returns the original function result if authorization checks pass.
    """
    def wrap(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            messages.error(request, "You must be logged in to view this page.")
            return redirect('login') 

        user_type = getattr(request.user, 'user_type', 'student')

        if user_type == 'student':
            return function(request, *args, **kwargs)
        else:
            messages.warning(request, "This page is for students only.")
            return redirect('admin_dashboard') 
    
    return wrap


def admin_required(function):
    """
    Decorator to ensure a user is logged in and is an 'admin'.
    
    Wraps a view function to enforce admin-only access. Checks if the user is authenticated
    and verifies their user_type is 'admin'. Redirects unauthenticated users to the login page
    and non-admin users (such as students) to the student dashboard with appropriate warning messages.
    Returns the original function result if authorization checks pass.
    """
    def wrap(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            messages.error(request, "You must be logged in to view this page.")
            return redirect('login') 

        user_type = getattr(request.user, 'user_type', 'student')

        if user_type == 'admin':
            return function(request, *args, **kwargs)
        else:
            messages.warning(request, "You do not have permission to access this page.")
            return redirect('student_dashboard') 
    
    return wrap
