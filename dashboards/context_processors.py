from supabase_client import supabase
from datetime import datetime

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


def notifications_context(request):
    """
    Adds unread notifications and their count to every request context.
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            # ✅ FIX: Fetch 5 newest notifications,
            # selecting 'is_read' but NOT filtering by it.
            response = supabase.table('notifications') \
                .select('id, message, link_url, created_at, is_read, products(image_url)') \
                .order('created_at', desc=True) \
                .limit(20) \
                .execute()
            
            # Fetch the TOTAL unread count for the "red dot"
            # We must use 'exact' count for this to work
            count_response = supabase.table('notifications') \
                .select('id', count='exact') \
                .eq('is_read', False) \
                .execute()

            # We must parse the date strings into datetime objects
            notifications_data = []
            if response.data:
                for item in response.data:
                    try:
                        # Convert ISO 8601 string to a timezone-aware datetime object
                        item['created_at'] = datetime.fromisoformat(item['created_at'])
                        notifications_data.append(item)
                    except (ValueError, TypeError, KeyError):
                        # Skip this notification if its date is missing or malformed
                        pass

            return {
                'notifications': response.data,
                'notification_count': count_response.count
            }
        except Exception as e:
            print(f"Error fetching notifications: {e}")
    
    # Return empty values if the user is not logged in or an error occurs
    return {'notifications': [], 'notification_count': 0}