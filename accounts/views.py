"""
Supabase-based authentication views for CIT Shop
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from supabase_client import supabase


def register(request):
    """Register a new user with Supabase Auth and create profile"""
    user_type = request.GET.get('type', 'student')
    
    if request.method == 'POST':
        user_type = request.POST.get('user_type', 'student')
        email = request.POST.get('email')
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
        full_name = request.POST.get('full_name')
        student_id = request.POST.get('student_id')
        staff_id = request.POST.get('staff_id')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        
        
        # Validation
        if not email or not email.endswith('@cit.edu'):
            messages.error(request, 'Only CIT institutional email addresses (@cit.edu) are allowed.')
            return render(request, 'registration/register.html', {'user_type': user_type})
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/register.html', {'user_type': user_type})
        
        if len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'registration/register.html', {'user_type': user_type})
        
        try:
            # Sign up user with Supabase
            response = supabase.auth.sign_up({
                'email': email,
                'password': password1,
                'options': {
                    'data': {
                        'full_name': full_name,
                        'user_type': user_type,
                        'student_id': student_id if user_type == 'student' else None,
                        'staff_id': staff_id if user_type == 'admin' else None,
                        'phone_number': phone_number,
                        'address': address,
                    }
                }
            })
            
            if response.user:
                # Create profile in user_profiles table
                try:
                    supabase.table('user_profiles').insert({
                        'user_id': response.user.id,
                        'email': email,
                        'full_name': full_name,
                        'user_type': user_type,
                        'student_id': student_id if user_type == 'student' else None,
                        'staff_id': staff_id if user_type == 'admin' else None,
                        'phone_number': phone_number,
                        'address': address,
                    }).execute()
                    print(f"✅ Profile created for user: {email}")
                except Exception as e:
                    print(f"⚠️ Profile creation failed: {e}")
                    # Don't block registration if profile creation fails
                
                messages.success(request, 'Registration successful! You can now login.')
                return redirect('login')
            else:
                messages.error(request, 'Registration failed. Please try again.')
                
        except Exception as e:
            error_message = str(e)
            if 'already registered' in error_message.lower():
                messages.error(request, 'This email is already registered.')
            else:
                messages.error(request, f'Registration error: {error_message}')
    
    return render(request, 'registration/register.html', {'user_type': user_type})


def login_view(request):
    """Login user with Supabase Auth, verify role, and sync profile"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        selected_role = request.POST.get('user_type') # Get role from the form

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'registration/login.html')
        
        try:
            # 1. Sign in user with Supabase
            response = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            if response.session:
                # 2. Get the user's actual role from Supabase metadata
                user_metadata = response.user.user_metadata
                actual_user_type = user_metadata.get('user_type', 'student') # Default to 'student' if not set

                # 3. CRITICAL: Check if the actual role matches the selected role
                if actual_user_type == selected_role:
                    # SUCCESS: Roles match. Proceed with login.
                    request.session['supa_access_token'] = response.session.access_token
                    request.session.save()
                    
                    # Redirect based on the verified user type
                    if actual_user_type == 'admin':
                        return redirect('admin_dashboard')
                    else:
                        return redirect('student_dashboard')
                else:
                    # ERROR: Role mismatch.
                    supabase.auth.sign_out() # Immediately invalidate the session
                    messages.error(request, f"Access restricted. Please use the '{actual_user_type.capitalize()}' login option.")
                    return redirect('login')

        except Exception as e:
            error_message = str(e)
            if 'Invalid login credentials' in error_message:
                messages.error(request, 'Invalid email or password.')
            elif 'Email not confirmed' in error_message:
                messages.error(request, 'Please verify your email first.')
            else:
                messages.error(request, 'An unexpected error occurred during login.')
            return render(request, 'registration/login.html')
    
    return render(request, 'registration/login.html')


def logout_view(request):
    """Logout user from Supabase"""
    try:
        # Sign out from Supabase
        supabase.auth.sign_out()
    except:
        pass
    
    # Clear Django session
    if 'supa_access_token' in request.session:
        del request.session['supa_access_token']
    
    return redirect('login')


def forgot_password(request):
    """Send password reset OTP via Supabase"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email or not email.endswith('@cit.edu'):
            messages.error(request, 'Only CIT institutional email addresses (@cit.edu) are allowed.')
            return render(request, 'registration/forgot_password.html')
        
        try:
            # Send OTP via Supabase (Supabase will send the email)
            supabase.auth.sign_in_with_otp({
                'email': email,
                'options': {
                    'should_create_user': False  # Don't create new user if email doesn't exist
                }
            })
            messages.success(request, f'An OTP has been sent to {email}. Please check your inbox.')
            return redirect('verify_otp', email=email)
            
        except Exception as e:
            # For security, don't reveal if email exists
            messages.success(request, f'If an account exists with {email}, an OTP has been sent.')
            return redirect('verify_otp', email=email)
    
    return render(request, 'registration/forgot_password.html')


def verify_otp(request, email):
    """Verify OTP sent by Supabase"""
    if request.method == 'POST':
        otp = request.POST.get('otp')
        
        if not otp or len(otp) != 6:
            messages.error(request, 'Please enter a valid 6-digit OTP.')
            return render(request, 'registration/verify_otp.html', {'email': email})
        
        try:
            # Verify OTP with Supabase
            response = supabase.auth.verify_otp({
                'email': email,
                'token': otp,
                'type': 'email'
            })
            
            if response.session:
                request.session['supa_access_token'] = response.session.access_token
                request.session['reset_email'] = email
                
                messages.success(request, 'OTP verified! Please enter your new password.')
                return redirect('reset_password')
            else:
                messages.error(request, 'Invalid or expired OTP.')
                
        except Exception as e:
            error_message = str(e)
            if 'expired' in error_message.lower():
                messages.error(request, 'OTP has expired. Please request a new one.')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'registration/verify_otp.html', {'email': email})


def reset_password(request):
    """Reset password after OTP verification"""
    if 'supa_access_token' not in request.session:
        messages.error(request, 'Please verify your OTP first.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/reset_password.html')
        
        if len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'registration/reset_password.html')
        
        try:
            # Update password in Supabase
            supabase.auth.update_user({
                'password': password1
            })
            
            # Clear session
            if 'reset_email' in request.session:
                del request.session['reset_email']
            if 'supa_access_token' in request.session:
                del request.session['supa_access_token']
            
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'registration/reset_password.html')

