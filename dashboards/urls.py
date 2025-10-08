from django.urls import path
from .views import student_dashboard, admin_dashboard, dashboard_redirect

urlpatterns = [
    path('', dashboard_redirect, name='dashboard_redirect'),
    path('student/', student_dashboard, name='student_dashboard'),
    path('admin/', admin_dashboard, name='admin_dashboard'),
]
