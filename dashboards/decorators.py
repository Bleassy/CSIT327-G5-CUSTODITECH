# In dashboards/decorators.py

from django.shortcuts import redirect
from django.contrib import messages

def admin_required(function):
    """
    Decorator to ensure a user is logged in and has an 'admin' role.
    """
    def wrap(request, *args, **kwargs):
        # 1. Check if user is logged in
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to view this page.")
            return redirect('login') 

        # 2. Check if user is an admin
        # ✅ FIX: Check for 'user_type' instead of 'role'
        user_meta = getattr(request.user, 'raw_user_meta_data', {})
        user_type = user_meta.get('user_type')

        if user_type == 'admin':
            # They are an admin, proceed to the view
            return function(request, *args, **kwargs)
        else:
            # They are logged in, but not an admin.
            messages.error(request, "You do not have permission to access this page.")
            return redirect('student_dashboard') 
    
    return wrap