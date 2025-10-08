from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_redirect(request):
    if hasattr(request.user, 'user_type'):
        if request.user.user_type == 'admin':
            return redirect('admin_dashboard')
    return redirect('student_dashboard')

@login_required
def student_dashboard(request):
    if hasattr(request.user, 'user_type') and request.user.user_type != 'student':
        return redirect('admin_dashboard')
    return render(request, 'dashboards/student_dashboard.html')

@login_required
def admin_dashboard(request):
    if hasattr(request.user, 'user_type') and request.user.user_type != 'admin':
        return redirect('student_dashboard')
    return render(request, 'dashboards/admin_dashboard.html')
