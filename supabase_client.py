import os
from supabase import create_client, Client

# --- Standard Client (for user-facing actions) ---
# This is the normal client, subject to Row-Level Security (RLS) policies.
# It uses the public 'anon' key.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# --- Service Role Client (for trusted backend actions) ---
# This is the powerful "super-admin" client that can bypass RLS.
# It uses the secret 'service_role' key.
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE")

if not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE must be set in .env file")

supabase_service: Client = create_client(
  SUPABASE_URL, SUPABASE_SERVICE_KEY
)

