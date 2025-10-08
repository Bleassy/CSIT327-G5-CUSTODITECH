from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'user_type', 'student_id', 'is_staff']
    list_filter = ['user_type', 'is_staff', 'is_active']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('user_type', 'student_id', 'phone_number', 'address')}),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('user_type', 'student_id', 'phone_number', 'address')}),
    )
