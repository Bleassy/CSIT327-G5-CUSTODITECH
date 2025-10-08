from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    register, CustomLoginView, forgot_password, 
    verify_otp, reset_password
)

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('verify-otp/<str:email>/', verify_otp, name='verify_otp'),
    path('reset-password/', reset_password, name='reset_password'),
]
