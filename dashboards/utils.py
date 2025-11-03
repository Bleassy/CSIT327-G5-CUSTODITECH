# In dashboards/utils.py

from .models import ActivityLog

def log_activity(user, action_type, details=None):
    """
    A helper function to create an activity log entry.
    Matches the ActivityLog model.
    """
    # Make sure the user is valid and authenticated
    if not user or not user.is_authenticated:
        return 

    try:
        # Create the log entry in the database
        ActivityLog.objects.create(
            user=user,
            action=action_type,  # Matches your model's 'action' field
            details=details or {} # Matches your model's 'details' field
        )
    except Exception as e:
        # Fail silently (print to console) so we don't crash the main view
        print(f"Error logging activity for user {user.id}: {e}")