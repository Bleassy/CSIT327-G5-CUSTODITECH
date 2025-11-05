

def profile_context(request):
    """
    Adds the user's profile data AND a display_name
    to every request context by reading it from request.user.
    """
    # Set default values
    context = {
        'profile': None,
        'display_name': 'Student' 
    }
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        
        # --- 1. Set fallback display_name from email ---
        try:
            if request.user.email:
                context['display_name'] = request.user.email.split('@')[0]
        except AttributeError:
            pass 

        # --- 2. Get profile data from the request.user object ---
        # The middleware already fetched this for us.
        try:
            profile_data = request.user.profile
            
            if profile_data:
                context['profile'] = profile_data
                
                # --- 3. Set real display_name from profile's full_name ---
                full_name = profile_data.get('full_name')
                if full_name and full_name.strip():
                    context['display_name'] = full_name.split(' ')[0]
            
            # If profile_data is empty or full_name is blank,
            # the email fallback we set above will be used.
        
        except Exception as e:
            # Fail silently if request.user.profile doesn't exist
            print(f"Error in profile context processor (reading from request.user): {e}") 
            pass 
            
    return context