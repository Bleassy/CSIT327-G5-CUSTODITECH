from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
import uuid # <-- Make sure this import is present

class CustomUser(AbstractUser):
    # This is the most important line in the file.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('admin', 'Admin'),
    )
    
    # Validators
    phone_regex = RegexValidator(
        regex=r'^\+63 \d{3} \d{3} \d{4}$',
        message="Phone number must be in format: +63 912 345 6789"
    )
    
    student_id_regex = RegexValidator(
        regex=r'^\d{2}-\d{4}-\d{3}$',
        message="Student ID must be in format: 12-3456-789"
    )
    
    staff_id_regex = RegexValidator(
        regex=r'^\d{2}-\d{4}-\d{3}$',
        message="Staff ID must be in format: 12-3456-789"
    )
    
    # User fields
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    student_id = models.CharField(max_length=50, blank=True, null=True, validators=[student_id_regex])
    staff_id = models.CharField(max_length=50, blank=True, null=True, validators=[staff_id_regex])
    phone_number = models.CharField(max_length=20, blank=True, validators=[phone_regex])
    address = models.CharField(max_length=200, blank=True)
    
    # OTP fields for password reset
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    # Make email unique and use it for authentication
    email = models.EmailField(unique=True)
    
    # Use email as the username field for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def is_otp_valid(self):
        """Check if OTP is still valid (5 minutes expiration)"""
        if self.otp_created_at:
            expiry_time = self.otp_created_at + timedelta(minutes=5)
            return timezone.now() < expiry_time
        return False
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.user_type}"


