"""FishOn Pipeline Configuration — loads env vars, initializes clients."""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from anthropic import Anthropic

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
ALERT_WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")

# Clients
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
