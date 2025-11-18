from supabase_client import supabase_service
import pytz
from datetime import datetime

def log_activity(user, action_type, details=None):
    """
    A helper function to create an activity log entry in the
    Supabase 'activity_log' table.
    
    Records user actions and their associated details in the database for audit trails
    and activity tracking. Accepts an authenticated user object, a string describing the
    action type (e.g., 'product_view', 'order_placed'), and optional details dictionary
    containing additional context about the action. Uses the service role client to bypass
    row-level security policies. Silently handles errors to prevent disrupting the main
    application flow if logging fails.
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
    
    Generates a dynamic greeting string based on the current local time in the Philippines.
    Evaluates the current hour to determine the appropriate time of day: returns "Good morning"
    for 5:00 AM - 11:59 AM, "Good afternoon" for 12:00 PM - 5:59 PM, and "Good evening" for
    all other hours. Useful for personalizing dashboard and UI welcome messages. Always uses
    Asia/Manila timezone to ensure consistency across all users.
    """
    ph_tz = pytz.timezone('Asia/Manila')
    current_hour = datetime.now(ph_tz).hour
    if 5 <= current_hour < 12: return "Good morning"
    if 12 <= current_hour < 18: return "Good afternoon"
    return "Good evening"
