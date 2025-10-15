import os
import requests
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
# ✅ IMPORT both supabase clients
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

        # Properties for Django Admin compatibility
        self.is_active = True
        self.is_staff = (self.user_type == 'admin')
        self.is_superuser = (self.user_type == 'admin')

    def get_full_name(self):
        # This now correctly reads the refreshed user_metadata
        return self.user_metadata.get('full_name', self.username)
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class SupabaseAuthMiddleware(MiddlewareMixin):
    """
    Middleware that validates Supabase JWT and ensures the user profile is fresh.
    """
    def process_request(self, request):
        token = request.session.get('supa_access_token')
        
        if not token:
            request.user = AnonymousUser()
            return
        
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_ANON_KEY')
            
            response = requests.get(
                f"{supabase_url}/auth/v1/user",
                headers={"Authorization": f"Bearer {token}", "apikey": supabase_key},
                timeout=5
            )
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get('id')

                # ✅ THE FIX IS HERE: Self-healing AND self-refreshing profile logic
                # On every request, fetch the latest profile from user_profiles table.
                try:
                    profile_res = supabase_service.table('user_profiles').select('full_name, user_type').eq('user_id', user_id).single().execute()
                    
                    if profile_res.data:
                        # If a profile exists, inject the LATEST data into user_metadata
                        # This ensures the name and role are always up-to-date.
                        if 'user_metadata' not in user_data:
                            user_data['user_metadata'] = {}
                        user_data['user_metadata']['full_name'] = profile_res.data.get('full_name')
                        user_data['user_metadata']['user_type'] = profile_res.data.get('user_type')
                    else:
                        # If no profile exists (edge case), create a basic one.
                        print(f"🛠️ No profile found for {user_data.get('email')}. Creating one now.")
                        initial_metadata = user_data.get('user_metadata', {})
                        supabase_service.table('user_profiles').insert({
                            'user_id': user_id,
                            'email': user_data.get('email'),
                            'full_name': initial_metadata.get('full_name', ''),
                            'user_type': initial_metadata.get('user_type', 'student')
                        }).execute()

                except Exception as profile_e:
                    print(f"--- FAILED TO SYNC PROFILE: {profile_e} ---")

                # Initialize the user object with the (potentially updated) user_data
                request.user = SupabaseUser(user_data)
            else:
                request.user = AnonymousUser()
                if 'supa_access_token' in request.session:
                    del request.session['supa_access_token']
                      
        except Exception as e:
            request.user = AnonymousUser()

