from supabase_client import supabase_service
import pytz
from datetime import datetime

def log_activity(user, action_type, details=None):
    """
    A helper function to create an activity log entry in the
    Supabase 'activity_log' table.
    """
    # Make sure the user is valid and authenticated
    if not user or not user.is_authenticated:
        return 

    try:
        # Use the supabase_service client to insert directly
        supabase_service.table('activity_log').insert({
            'user_id': str(user.id),  # Use str() to be safe with UUIDs
            'action': action_type,
            'details': details or {}
        }).execute()
    except Exception as e:
        # Fail silently (print to console) so we don't crash the main view
        print(f"Error logging activity for user {user.id}: {e}")


def get_greeting():
    """
    Returns a time-appropriate greeting (Good morning, afternoon, or evening)
    based on the current hour in the 'Asia/Manila' timezone.
    """
    ph_tz = pytz.timezone('Asia/Manila')
    current_hour = datetime.now(ph_tz).hour
    if 5 <= current_hour < 12: return "Good morning"
    if 12 <= current_hour < 18: return "Good afternoon"
    return "Good evening"
