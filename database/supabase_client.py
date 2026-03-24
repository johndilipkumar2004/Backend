from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://fosiooudtagavnsgpvhj.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvc2lvb3VkdGFnYXZuc2dwdmhqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4NjcwNzEsImV4cCI6MjA4ODQ0MzA3MX0.2UihNi6oyrxjcx1XGsB7HJcYnonbCTT6FKoOsxbPQK0")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvc2lvb3VkdGFnYXZuc2dwdmhqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Mjg2NzA3MSwiZXhwIjoyMDg4NDQzMDcxfQ.wORJJef2Pq1D8PuI_-TmyWbVtELTMgt-ver-29McNxU")

# Standard client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Admin client - bypasses RLS
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_supabase() -> Client:
    return supabase


def get_supabase_admin() -> Client:
    return supabase_admin
