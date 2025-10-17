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
        # ✅ THE FIX IS HERE: Let Django's system handle staff/superuser for its own admin
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
    """
    def process_request(self, request):
        
        # ✅ THE FIX IS HERE: Add this check at the very top.
        # If the path is for the Django admin, let Django's own auth handle it.
        # We also check if a user is already authenticated by Django's session middleware.
        if request.path.startswith('/admin'):
            # If Django's session middleware already authenticated a user, just return.
            if hasattr(request, 'user') and request.user.is_authenticated:
                return
        
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

                try:
                    profile_res = supabase_service.table('user_profiles').select('full_name, user_type').eq('user_id', user_id).single().execute()
                    
                    if profile_res.data:
                        if 'user_metadata' not in user_data:
                            user_data['user_metadata'] = {}
                        user_data['user_metadata']['full_name'] = profile_res.data.get('full_name')
                        user_data['user_metadata']['user_type'] = profile_res.data.get('user_type')
                    else:
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

                request.user = SupabaseUser(user_data)
            else:
                request.user = AnonymousUser()
                if 'supa_access_token' in request.session:
                    del request.session['supa_access_token']
                          
        except Exception as e:
            request.user = AnonymousUser()