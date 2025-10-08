from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import CustomUser


class StudentRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Juan Dela Cruz',
            'class': 'form-control'
        })
    )
    
    student_id = forms.CharField(
        max_length=50,
        required=True,
        validators=[RegexValidator(
            regex=r'^\d{2}-\d{4}-\d{3}$',
            message='Student ID must be in format: 12-3456-789'
        )],
        widget=forms.TextInput(attrs={
            'placeholder': '12-3456-789',
            'pattern': r'\d{2}-\d{4}-\d{3}',
            'class': 'form-control'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'juan.delacruz@cit.edu',
            'class': 'form-control'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        validators=[RegexValidator(
            regex=r'^\+63 \d{3} \d{3} \d{4}$',
            message='Phone number must be in format: +63 912 345 6789'
        )],
        widget=forms.TextInput(attrs={
            'placeholder': '+63 912 345 6789',
            'pattern': r'\+63 \d{3} \d{3} \d{4}',
            'class': 'form-control'
        })
    )
    
    address = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Cebu City, Philippines',
            'class': 'form-control'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Minimum 6 characters',
            'class': 'form-control'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Re-enter your password',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'student_id', 'email', 'phone_number', 'address', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not email.endswith('@cit.edu'):
            raise ValidationError('Only CIT institutional email addresses (@cit.edu) are allowed.')
        
        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        
        # Split full name into first and last name
        full_name = self.cleaned_data.get('full_name', '')
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Set username as email prefix (for display purposes)
        user.username = self.cleaned_data['email'].split('@')[0]
        user.email = self.cleaned_data['email']
        user.student_id = self.cleaned_data['student_id']
        user.phone_number = self.cleaned_data['phone_number']
        user.address = self.cleaned_data['address']
        
        if commit:
            user.save()
        return user


class AdminRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Maria Santos',
            'class': 'form-control'
        })
    )
    
    staff_id = forms.CharField(
        max_length=50,
        required=True,
        validators=[RegexValidator(
            regex=r'^\d{2}-\d{4}-\d{3}$',
            message='Staff ID must be in format: 12-3456-789'
        )],
        widget=forms.TextInput(attrs={
            'placeholder': '12-3456-789',
            'pattern': r'\d{2}-\d{4}-\d{3}',
            'class': 'form-control'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'maria.santos@cit.edu',
            'class': 'form-control'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        validators=[RegexValidator(
            regex=r'^\+63 \d{3} \d{3} \d{4}$',
            message='Phone number must be in format: +63 912 345 6789'
        )],
        widget=forms.TextInput(attrs={
            'placeholder': '+63 912 345 6789',
            'pattern': r'\+63 \d{3} \d{3} \d{4}',
            'class': 'form-control'
        })
    )
    
    address = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Cebu City, Philippines',
            'class': 'form-control'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Minimum 6 characters',
            'class': 'form-control'
        })
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Re-enter your password',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'staff_id', 'email', 'phone_number', 'address', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not email.endswith('@cit.edu'):
            raise ValidationError('Only CIT institutional email addresses (@cit.edu) are allowed.')
        
        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'admin'
        
        # Split full name into first and last name
        full_name = self.cleaned_data.get('full_name', '')
        name_parts = full_name.split(' ', 1)
        user.first_name = name_parts[0]
        user.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Set username as email prefix (for display purposes)
        user.username = self.cleaned_data['email'].split('@')[0]
        user.email = self.cleaned_data['email']
        user.staff_id = self.cleaned_data['staff_id']
        user.phone_number = self.cleaned_data['phone_number']
        user.address = self.cleaned_data['address']
        
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    """Custom authentication form that uses email instead of username"""
    username = forms.EmailField(
        label='CIT Institutional Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'your.email@cit.edu',
            'class': 'form-control',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'class': 'form-control'
        })
    )
