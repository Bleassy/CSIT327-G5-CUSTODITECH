from django.urls import path
from .views import (
    register, login_view, logout_view, forgot_password, 
    verify_otp, reset_password
)

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('verify-otp/<str:email>/', verify_otp, name='verify_otp'),
    path('reset-password/', reset_password, name='reset_password'),
]
