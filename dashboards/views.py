from django.shortcuts import render, redirect
from django.contrib import messages


def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user type"""
    # Check if user is authenticated via Supabase
    if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('login')
    
    # Redirect based on user type
    user_type = getattr(request.user, 'user_type', 'student')
    if user_type == 'admin':
        return redirect('admin_dashboard')
    return redirect('student_dashboard')


def student_dashboard(request):
    """Student dashboard view"""
    # Check authentication
    if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('login')
    
    # Restrict admin access
    user_type = getattr(request.user, 'user_type', 'student')
    if user_type == 'admin':
        return redirect('admin_dashboard')

    user = request.user

    # --- 🧠 Safely get the user's name (Supabase compatible) ---
    name = None
    if hasattr(user, 'user_metadata'):
        meta = getattr(user, 'user_metadata', {}) or {}
        name = (
            meta.get('full_name')
            or meta.get('name')
            or meta.get('first_name')
            or meta.get('username')
        )

    # Fallbacks
    raw_name = (
        name
        or getattr(user, 'username', None)
        or getattr(user, 'email', None)
        or "Wildcat"
    )

    # ✅ Extract only the first name (split by space)
    display_name = raw_name.split()[0] if isinstance(raw_name, str) else "Wildcat"

    # Greeting logic
    greeting = "Welcome back" if request.session.get('has_logged_in_before') else "Welcome"
    request.session['has_logged_in_before'] = True

    context = {
        'display_name': display_name,
        'greeting': greeting,
    }
    return render(request, 'dashboards/student_dashboard.html', context)






def admin_dashboard(request):
    """Admin dashboard view"""
    # ✅ Authentication check
    if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('login')

    # ✅ Restrict non-admins
    user_type = getattr(request.user, 'user_type', 'student')
    if user_type != 'admin':
        messages.warning(request, 'You do not have access to the admin dashboard.')
        return redirect('student_dashboard')

    user = request.user

    # --- 🧠 Safely get the admin's name (Supabase compatible) ---
    name = None
    if hasattr(user, 'user_metadata'):
        meta = getattr(user, 'user_metadata', {}) or {}
        name = (
            meta.get('full_name')
            or meta.get('name')
            or meta.get('first_name')
            or meta.get('username')
        )

    # Fallbacks for name
    raw_name = (
        name
        or getattr(user, 'username', None)
        or getattr(user, 'email', None)
        or "Admin"
    )

    # ✅ Extract only first name
    display_name = raw_name.split()[0] if isinstance(raw_name, str) else "Admin"

    # ✅ Greeting logic (same as student dashboard)
    greeting = "Welcome back" if request.session.get('has_logged_in_before_admin') else "Welcome"
    request.session['has_logged_in_before_admin'] = True

    # Dummy stats (replace with DB data later)
    stats = {
        'total_products': 250,
        'total_buyers': 120,
        'total_reservations': 85,
        'total_orders': 150
    }

    context = {
        'display_name': display_name,
        'greeting': greeting,
        'stats': stats,
    }

    return render(request, 'dashboards/admin_dashboard.html', context)


