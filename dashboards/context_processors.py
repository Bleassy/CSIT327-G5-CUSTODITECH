from supabase_client import supabase

def profile_context(request):
    """
    Adds the user's profile data (like avatar_url) to every
    request context, so it's available in the base templates.
    """
    context = {'profile': None} # Start with an empty profile
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            user_id = request.user.id
            # Fetch only the fields we need in the header for speed
            response = supabase.table('user_profiles').select('avatar_url', 'full_name').eq('user_id', user_id).single().execute()
            if response.data:
                context['profile'] = response.data
        except Exception as e:
            # Fail silently if the profile doesn't exist yet or there's an error
            print(f"Error in profile context processor: {e}") 
            pass 
            
    return context