# In dashboards/context_processors.py

from supabase_client import supabase

def profile_context(request):
    """
    Adds the user's profile data AND a display_name
    to every request context.
    """
    # Set default values
    context = {
        'profile': None,
        'display_name': 'Student'  # A safe, generic default
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        
        # --- 1. Try to get email as a better fallback (if it exists) ---
        try:
            if request.user.email:
                # Use the part before the '@' as a fallback name
                context['display_name'] = request.user.email.split('@')[0]
        except AttributeError:
             pass # 'Student' will remain the fallback

        # --- 2. Try to get the real name from the profile table ---
        try:
            user_id = request.user.id
            response = supabase.table('user_profiles').select('avatar_url', 'full_name').eq('user_id', user_id).single().execute()
            
            if response.data:
                context['profile'] = response.data
                
                # Check if 'full_name' exists and is not just an empty string
                if response.data.get('full_name') and response.data['full_name'].strip():
                    # Use the first word of their full name
                    context['display_name'] = response.data['full_name'].split(' ')[0]
                # If no full_name, the email fallback we set above will be used
        
        except Exception as e:
            # Fail silently if the profile doesn't exist yet or there's an error
            print(f"Error in profile context processor: {e}") 
            pass 
            
    return context