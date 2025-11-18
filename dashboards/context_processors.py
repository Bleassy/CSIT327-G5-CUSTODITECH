from supabase_client import supabase
from datetime import datetime

def profile_context(request):
    """
    Context processor that adds user profile data to template context.
    
    Retrieves the authenticated user's profile information from the request object
    and extracts key data such as full name and email. Provides a display name
    (fallback to email prefix or default 'Student') that can be used in templates.
    Gracefully handles missing profile data by returning default values.
    Returns a dictionary containing 'profile' (user profile object) and 'display_name' (user-friendly name).
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
        try:
            profile_data = request.user.profile
            
            if profile_data:
                context['profile'] = profile_data
                
                # --- 3. Set real display_name from profile's full_name ---
                full_name = profile_data.get('full_name')
                if full_name and full_name.strip():
                    context['display_name'] = full_name.split(' ')[0]
            
        
        except Exception as e:
            # Fail silently if request.user.profile doesn't exist
            print(f"Error in profile context processor (reading from request.user): {e}") 
            pass 
            
    return context


def notifications_context(request):
    """
    Context processor that adds unread notifications to template context.
    
    Fetches the 20 most recent notifications for the authenticated user from Supabase,
    including notification details (message, link, timestamp, read status) and associated
    product images. Separately queries the total count of unread notifications for use
    in UI indicators (red dot badges). Converts ISO 8601 timestamp strings to Python
    datetime objects for proper template formatting and filtering.
    Returns a dictionary containing 'notifications' (list of notification objects)
    and 'notification_count' (integer count of unread notifications).
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            # selecting 'is_read' but NOT filtering by it.
            response = supabase.table('notifications') \
                .select('id, message, link_url, created_at, is_read, products(image_url)') \
                .order('created_at', desc=True) \
                .limit(20) \
                .execute()
            
            # Fetch the TOTAL unread count for the "red dot"
            count_response = supabase.table('notifications') \
                .select('id', count='exact') \
                .eq('is_read', False) \
                .execute()

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