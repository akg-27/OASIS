from supabase import create_client
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Read Supabase keys
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)