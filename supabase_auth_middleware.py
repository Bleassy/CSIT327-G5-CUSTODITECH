"""
Middleware to authenticate Supabase users in Django
"""
import os
import requests
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser

class SupabaseUser:
    """Custom user object for Supabase authenticated users"""
    def __init__(self, user_data):
        self.is_authenticated = True
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.user_metadata = user_data.get('user_metadata', {})
        self.username = self.email.split('@')[0] if self.email else 'user'
        self.user_type = self.user_metadata.get('user_type', 'student')
        
    def get_full_name(self):
        return self.user_metadata.get('full_name', self.username)

class SupabaseAuthMiddleware(MiddlewareMixin):
    """
    Middleware that validates Supabase JWT from session
    and sets request.user to SupabaseUser or AnonymousUser
    """
    def process_request(self, request):
        token = request.session.get('supa_access_token')
        
        print(f"🔍 Middleware - Path: {request.path}, Token exists: {bool(token)}")
        
        if not token:
            request.user = AnonymousUser()
            print("❌ No token - AnonymousUser")
            return
        
        try:
            # Verify token by calling Supabase user endpoint
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_ANON_KEY')
            
            response = requests.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": supabase_key
                },
                timeout=5
            )
            
            print(f"📡 Supabase API response: {response.status_code}")
            
            if response.status_code == 200:
                user_data = response.json()
                request.user = SupabaseUser(user_data)
                print(f"✅ Authenticated: {request.user.email}, type: {request.user.user_type}")
            else:
                # Token invalid or expired
                request.user = AnonymousUser()
                if 'supa_access_token' in request.session:
                    del request.session['supa_access_token']
                print(f"⚠️ Token invalid - cleared session")
                    
        except Exception as e:
            print(f"❌ Middleware error: {e}")
            request.user = AnonymousUser()
