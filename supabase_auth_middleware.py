# supabase_auth_middleware.py

import os
import requests
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from supabase_client import supabase, supabase_service

class SupabaseUser:
    """Custom user object for Supabase authenticated users"""
    def __init__(self, user_data):
        self.is_authenticated = True
        self.id = user_data.get('id')
        self.pk = self.id # Alias for Django admin compatibility
        self.email = user_data.get('email')
        self.user_metadata = user_data.get('user_metadata', {})
        self.username = self.email.split('@')[0] if self.email else 'user'
        self.user_type = self.user_metadata.get('user_type', 'student')

        # Store the full profile data from the middleware
        self.profile = user_data.get('profile_data', {}) 

        # Properties for Django Admin compatibility
        self.is_active = True
        # This SupabaseUser is for the front-facing app, not the /admin/ panel.
        self.is_staff = False
        self.is_superuser = False

    def get_full_name(self):
        # This now correctly reads the refreshed user_metadata
        return self.user_metadata.get('full_name', self.username)
    
    # We can keep these for any custom checks, but they won't grant /admin/ access
    def has_perm(self, perm, obj=None):
        return self.user_type == 'admin'

    def has_module_perms(self, app_label):
        return self.user_type == 'admin'


class SupabaseAuthMiddleware(MiddlewareMixin):
    """
    Middleware that validates Supabase JWT and ensures the user profile is fresh.
    This middleware now handles automatic token refreshing.
    """
    def process_request(self, request):
        
        # --- This admin check is good, keep it ---
        if request.path.startswith('/admin'):
            if hasattr(request, 'user') and request.user.is_authenticated:
                return
        # --- End of admin check ---

        # Get both tokens from the session
        access_token = request.session.get('supa_access_token')
        refresh_token = request.session.get('supa_refresh_token')

        if not access_token or not refresh_token:
            request.user = AnonymousUser()
            return
        
        try:
            # Set the session on the client.
            supabase.auth.set_session(access_token, refresh_token)
            
            # Use the client's get_user() method.
            user_response = supabase.auth.get_user()
            
            # Check if the session was refreshed and update it in Django
            current_session = supabase.auth.get_session()
            if current_session and current_session.access_token != access_token:
                print("🛠️ Supabase session was refreshed. Updating Django session.")
                request.session['supa_access_token'] = current_session.access_token
                request.session['supa_refresh_token'] = current_session.refresh_token
                request.session.save()

            # Get user data in the new format
            user_data = user_response.user.model_dump() 
            user_id = user_data.get('id')

            try:
                # Select avatar_url here since we need it in the context
                profile_res = supabase_service.table('user_profiles').select('full_name, user_type, avatar_url').eq('user_id', user_id).single().execute()
                
                if profile_res.data:
                    if 'user_metadata' not in user_data:
                        user_data['user_metadata'] = {}
                    user_data['user_metadata']['full_name'] = profile_res.data.get('full_name')
                    user_data['user_metadata']['user_type'] = profile_res.data.get('user_type')
                    
                    # Attach the full profile data to user_data
                    user_data['profile_data'] = profile_res.data 
                else:
                    print(f"🛠️ No profile found for {user_data.get('email')}. Creating one now.")
                    initial_metadata = user_data.get('user_metadata', {})
                    
                    # Create the profile in the DB
                    new_profile_data = {
                        'user_id': user_id,
                        'email': user_data.get('email'),
                        'full_name': initial_metadata.get('full_name', ''),
                        'user_type': initial_metadata.get('user_type', 'student')
                    }
                    supabase_service.table('user_profiles').insert(new_profile_data).execute()
                    
                    # Attach this new profile data (with avatar_url=None by default)
                    new_profile_data['avatar_url'] = None # Add this since it wasn't in the insert
                    user_data['profile_data'] = new_profile_data

            except Exception as profile_e:
                print(f"--- FAILED TO SYNC PROFILE: {profile_e} ---")
                # Set an empty profile so request.user.profile doesn't fail
                user_data['profile_data'] = {} 
            # --- End of profile-syncing logic ---

            request.user = SupabaseUser(user_data)

        except Exception as e:
            # This will catch errors if the refresh_token is also invalid
            print(f"--- Supabase Auth Middleware Error: {e} ---")
            request.user = AnonymousUser()
            # Clear the invalid tokens from the Django session
            if 'supa_access_token' in request.session:
                del request.session['supa_access_token']
            if 'supa_refresh_token' in request.session:
                del request.session['supa_refresh_token']