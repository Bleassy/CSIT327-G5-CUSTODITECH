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
    # Check if user is authenticated via Supabase
    if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('login')
    
    # Check if user is admin trying to access student dashboard
    user_type = getattr(request.user, 'user_type', 'student')
    if user_type == 'admin':
        return redirect('admin_dashboard')
    
    return render(request, 'dashboards/student_dashboard.html')


def admin_dashboard(request):
    """Admin dashboard view"""
    # Check if user is authenticated via Supabase
    if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('login')
    
    # Check if user is student trying to access admin dashboard
    user_type = getattr(request.user, 'user_type', 'student')
    if user_type != 'admin':
        return redirect('student_dashboard')
    
    return render(request, 'dashboards/admin_dashboard.html')
