from django.shortcuts import redirect
from django.contrib import messages

def student_required(function):
    """
    Decorator to ensure a user is logged in and is a 'student'.
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
