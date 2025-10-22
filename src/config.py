"""
Configuration file for GST scraper
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GST Portal URLs
GST_BASE_URL = "https://services.gst.gov.in"
GST_SEARCH_URL = f"{GST_BASE_URL}/services/searchtp"

# Scraping Configuration
DELAY_BETWEEN_REQUESTS = 2  # seconds
MAX_RETRIES = 3
TIMEOUT = 30  # seconds

# Output Configuration
OUTPUT_DIR = "data"
LOG_DIR = "logs"
OUTPUT_FORMAT = "csv"  # csv or json

# User Agent Rotation
USE_ROTATING_USER_AGENTS = True

# Email Notifications (Optional)
ENABLE_EMAIL = os.getenv("ENABLE_EMAIL", "false").lower() == "true"
EMAIL_TO = os.getenv("EMAIL_TO", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Debug Mode
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
