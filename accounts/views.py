import random
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from .forms import StudentRegistrationForm, AdminRegistrationForm
from .models import CustomUser


def register(request):
    user_type = request.GET.get('type', 'student')
    
    if request.method == 'POST':
        user_type = request.POST.get('user_type', 'student')
        
        if user_type == 'student':
            form = StudentRegistrationForm(request.POST)
        else:
            form = AdminRegistrationForm(request.POST)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            
            if user.user_type == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('student_dashboard')
    else:
        if user_type == 'student':
            form = StudentRegistrationForm()
        else:
            form = AdminRegistrationForm()
    
    return render(request, 'registration/register.html', {
        'form': form,
        'user_type': user_type
    })


from .forms import StudentRegistrationForm, AdminRegistrationForm, EmailAuthenticationForm

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = EmailAuthenticationForm  # Use our custom form
    
    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if hasattr(user, 'user_type'):
                if user.user_type == 'admin':
                    return '/dashboard/admin/'
                else:
                    return '/dashboard/student/'
        return '/dashboard/student/'

# OTP Helper Function
def generate_otp():
    """Generate a random 6-digit OTP"""
    return str(random.randint(100000, 999999))


# Forgot Password Views
def forgot_password(request):
    """Request OTP for password reset"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Check if email ends with @cit.edu
        if not email.endswith('@cit.edu'):
            messages.error(request, 'Only CIT institutional email addresses (@cit.edu) are allowed.')
            return render(request, 'registration/forgot_password.html')
        
        try:
            user = CustomUser.objects.get(email=email)
            
            # Generate and save OTP
            otp = generate_otp()
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()
            
            print(f"DEBUG: Generated OTP {otp} for user {user.email}")  # Debug output
            
            # Send OTP via email
            subject = 'Password Reset OTP - CIT Shop'
            message = f'''Hello {user.get_full_name() or user.username},

Your OTP for password reset is: {otp}

This OTP is valid for 5 minutes only.

If you didn't request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
CIT Shop Team - Wildcats'''
            
            try:
                result = send_mail(
                    subject,
                    message,
                    'lanticsev@gmail.com',  # Explicitly use your verified SendGrid sender
                    [email],
                    fail_silently=False,
                )
                print(f"DEBUG: Email send result: {result}")  # 1 = success, 0 = failed
                
                if result == 1:
                    messages.success(request, f'OTP has been sent to {email}. Please check your inbox.')
                    return redirect('verify_otp', email=email)
                else:
                    messages.error(request, 'Failed to send email. Email service returned 0.')
                    print(f"DEBUG: Email failed - check terminal for errors")
                    
            except Exception as e:
                messages.error(request, f'Failed to send email. Error: {str(e)}')
                print(f"DEBUG: Email exception: {type(e).__name__}: {str(e)}")  # Print full error to console
                import traceback
                traceback.print_exc()  # Print full traceback
                
        except CustomUser.DoesNotExist:
            # For security, don't reveal if email exists or not
            messages.error(request, 'If an account exists with this email, an OTP has been sent.')
    
    return render(request, 'registration/forgot_password.html')


def verify_otp(request, email):
    """Verify OTP and allow password reset"""
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid request.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        
        # Check if OTP matches and is still valid
        if user.otp == otp_input:
            if user.is_otp_valid():
                # OTP is correct and valid
                request.session['reset_user_id'] = user.id
                messages.success(request, 'OTP verified! Please enter your new password.')
                return redirect('reset_password')
            else:
                messages.error(request, 'OTP has expired. Please request a new one.')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'registration/verify_otp.html', {'email': email})


def reset_password(request):
    """Reset password after OTP verification"""
    # Check if user has verified OTP
    if 'reset_user_id' not in request.session:
        messages.error(request, 'Please verify your OTP first.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validate passwords match
        if password1 != password2:
            messages.error(request, 'Passwords do not match. Please try again.')
            return render(request, 'registration/reset_password.html')
        
        # Validate password length
        if len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'registration/reset_password.html')
        
        try:
            user = CustomUser.objects.get(id=request.session['reset_user_id'])
            
            # Set new password
            user.set_password(password1)
            
            # Clear OTP fields
            user.otp = None
            user.otp_created_at = None
            user.save()
            
            # Clear session
            del request.session['reset_user_id']
            
            messages.success(request, 'Password reset successful! You can now login with your new password.')
            return redirect('login')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found. Please try again.')
            del request.session['reset_user_id']
            return redirect('forgot_password')
    
    return render(request, 'registration/reset_password.html')


def resend_otp(request, email):
    """Resend OTP to user's email"""
    try:
        user = CustomUser.objects.get(email=email)
        
        # Generate new OTP
        otp = generate_otp()
        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save()
        
        print(f"DEBUG: Resending OTP {otp} for user {user.email}")  # Debug output
        
        # Send OTP via email
        subject = 'Password Reset OTP (Resent) - CIT Shop'
        message = f'''Hello {user.get_full_name() or user.username},

Your new OTP for password reset is: {otp}

This OTP is valid for 5 minutes only.

If you didn't request this password reset, please ignore this email.

Best regards,
CIT Shop Team - Wildcats'''
        
        try:
            result = send_mail(
                subject,
                message,
                'lanticsev@gmail.com',  # Explicitly use your verified SendGrid sender
                [email],
                fail_silently=False,
            )
            print(f"DEBUG: Resend email result: {result}")
            
            if result == 1:
                messages.success(request, 'A new OTP has been sent to your email.')
            else:
                messages.error(request, 'Failed to resend OTP.')
                
        except Exception as e:
            messages.error(request, f'Failed to resend OTP. Error: {str(e)}')
            print(f"DEBUG: Resend exception: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('verify_otp', email=email)
