from django.urls import path
from . import views

urlpatterns = [
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),
     path('admin/products/add/', views.add_product, name='add_product'),
]
