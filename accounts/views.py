"""
Supabase-based authentication views for CIT Shop
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from supabase_client import supabase
import re
from django.http import JsonResponse


def register(request):
    """Register a new user with Supabase Auth and create profile"""
    user_type = request.GET.get('type', 'student') # Keep this if needed elsewhere
    context = {'user_type': user_type}

    if request.method == 'POST':
        form_data = request.POST.copy()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Pass form_data back only for non-AJAX errors
        if not is_ajax:
            context['form_data'] = form_data

        email = form_data.get('email')
        password1 = form_data.get('password1', '').strip()
        password2 = form_data.get('password2', '').strip()
        full_name = form_data.get('full_name')
        student_id = form_data.get('student_id')
        phone_number = form_data.get('phone_number')
        address = form_data.get('address')

        # --- Consolidated Validation ---
        error_list = [] # Store errors for JSON response
        if full_name and not re.match(r"^[a-zA-ZñÑ. ]+$", full_name):
            error_list.append('Full name can only contain letters, spaces, and periods.')
        if not email or not email.endswith('@cit.edu'):
            error_list.append('Only CIT institutional email addresses (@cit.edu) are allowed.')
        if phone_number:
            phone_pattern = re.compile(r"^\+63 9\d{2} \d{3} \d{4}$")
            if not phone_pattern.match(phone_number):
                error_list.append('Please enter a valid Philippine mobile number format: +63 912 345 6789.')
        if address and address.count(',') < 3: # Check for 3 commas (4 parts)
             error_list.append('Address format: Street, Barangay, City, Province.')
        if len(password1) < 8:
            error_list.append('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password1):
            error_list.append('Password needs an uppercase letter.')
        if not re.search(r'[a-z]', password1):
            error_list.append('Password needs a lowercase letter.')
        if not re.search(r'[0-9]', password1):
            error_list.append('Password needs a number.')
        if not re.search(r'[@$!%*?&]', password1):
             error_list.append('Password needs a special character (@$!%*?&).')
        if password1 != password2:
            error_list.append('Passwords do not match.')
        

        # --- Handle Validation Results ---
        if error_list:
            if is_ajax:
                # Return JSON with list of errors
                return JsonResponse({'success': False, 'errors': error_list}, status=400)
            else:
                # Add errors to Django messages for non-AJAX
                for error in error_list:
                    messages.error(request, error)
                return render(request, 'registration/register.html', context)
        # --- End Validation ---

        # --- Try Supabase Sign Up ---
        try:
            response = supabase.auth.sign_up({
                'email': email,
                'password': password1,
                'options': {
                    'data': {
                        'full_name': full_name,
                        'user_type': 'student',
                        'student_id': student_id,
                        'phone_number': phone_number,
                        'address': address,
                    }
                }
            })

            if response.user:
                # Try creating profile (best effort)
                try:
                    supabase.table('user_profiles').insert({
                        'user_id': response.user.id, 'email': email, 'full_name': full_name,
                        'user_type': 'student', 'student_id': student_id,
                        'phone_number': phone_number, 'address': address,
                    }).execute()
                    print(f"✅ Profile created for user: {email}")
                except Exception as profile_e:
                    print(f"⚠️ Profile creation failed: {profile_e}") # Log only

                # --- Handle SUCCESS ---
                success_msg = 'Registration successful!'
                login_url = redirect('login').url

                if is_ajax:
                    # Return JSON success with redirect URL
                    redirect_url_with_message = f"{login_url}?message={success_msg}"
                    return JsonResponse({'success': True, 'redirect_url': redirect_url_with_message, 'message': success_msg})
                else:
                    messages.success(request, success_msg)
                    return redirect('login')
            else:
                # Supabase sign_up didn't return a user but didn't raise an exception? Unlikely.
                raise Exception("Registration failed unexpectedly.")

        except Exception as e:
            error_message = str(e)
            user_facing_error = 'An unexpected error occurred during registration.' # Default
            if 'already registered' in error_message.lower():
                user_facing_error = 'This email is already registered.'
            elif 'check your email' in error_message.lower(): # Catch Supabase rate limits or config issues
                 user_facing_error = 'Could not send verification email. Please try again later.'

            print(f"--- REGISTER ERROR: {error_message} ---") # Log actual error

            # --- Handle FAILURE ---
            if is_ajax:
                return JsonResponse({'success': False, 'errors': [user_facing_error]}, status=400)
            else:
                messages.error(request, user_facing_error)
                return render(request, 'registration/register.html', context)

    # Handle GET request
    return render(request, 'registration/register.html', context)


@require_http_methods(["GET", "POST"]) # Allow GET for initial page load
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        selected_role = request.POST.get('user_type')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not email or not password:
            error_msg = 'Email and password are required.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            else:
                messages.error(request, error_msg)
                return render(request, 'registration/login.html')

        try:
            # 1. Sign in user with Supabase
            response = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })

            if response.session:
                # 2. Get user's actual role
                user_metadata = response.user.user_metadata
                actual_user_type = user_metadata.get('user_type', 'student')

                # 3. Check role match
                if actual_user_type == selected_role:
                    # SUCCESS: Roles match
                    request.session['supa_access_token'] = response.session.access_token
                    request.session.save()

                    # Determine redirect URL
                    redirect_url = None
                    if actual_user_type == 'admin':
                        redirect_url = redirect('admin_dashboard').url # Get URL from redirect object
                    else:
                        redirect_url = redirect('student_dashboard').url

                    if is_ajax:
                        # Return success JSON with redirect URL
                        return JsonResponse({'success': True, 'redirect_url': redirect_url})
                    else:
                        # Standard redirect for non-AJAX
                        return redirect(redirect_url)
                else:
                    # ERROR: Role mismatch
                    supabase.auth.sign_out() # Invalidate session
                    error_msg = f"Access restricted. Please use the '{actual_user_type.capitalize()}' login option."
                    if is_ajax:
                        return JsonResponse({'success': False, 'error': error_msg}, status=403) # 403 Forbidden
                    else:
                        messages.error(request, error_msg)
                        return redirect('login') # Redirect back to login page

        except Exception as e:
            error_message = str(e)
            user_facing_error = 'An unexpected error occurred during login.' # Default error

            if 'Invalid login credentials' in error_message:
                user_facing_error = 'Invalid email or password.'
            elif 'Email not confirmed' in error_message:
                user_facing_error = 'Please verify your email first.'
            # Add other specific Supabase error checks if needed

            print(f"--- LOGIN ERROR: {error_message} ---") # Log the actual error for debugging

            if is_ajax:
                # Return error JSON
                return JsonResponse({'success': False, 'error': user_facing_error}, status=401) # 401 Unauthorized
            else:
                # Standard message and render for non-AJAX
                messages.error(request, user_facing_error)
                return render(request, 'registration/login.html')

    # Handle GET request (initial page load)
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

    messages.success(request, "You have been logged out successfully.")
    
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

            messages.success(request, 'Your password has been successfully reset. Please log in.')
            
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'registration/reset_password.html')

