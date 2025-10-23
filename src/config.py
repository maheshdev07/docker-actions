"""
Configuration settings for docker-actions GST scraper
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# GST Portal Configuration
GST_BASE_URL = "https://services.gst.gov.in"
GST_SEARCH_URL = f"{GST_BASE_URL}/services/searchtp"
GST_TAXPAYER_URL = f"{GST_BASE_URL}/services/api/search/taxpayersearch"

# Scraping Configuration
DELAY_BETWEEN_REQUESTS = int(os.getenv("DELAY_BETWEEN_REQUESTS", "2"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
USER_AGENT_ROTATION = os.getenv("USER_AGENT_ROTATION", "true").lower() == "true"

# Output Configuration
OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "both")  # csv, json, or both
INCLUDE_TIMESTAMP = os.getenv("INCLUDE_TIMESTAMP", "true").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_ROTATION = os.getenv("LOG_ROTATION", "1 day")
LOG_RETENTION = os.getenv("LOG_RETENTION", "7 days")

# Email Notification Configuration (Optional)
ENABLE_EMAIL = os.getenv("ENABLE_EMAIL", "false").lower() == "true"
EMAIL_TO = os.getenv("EMAIL_TO", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Application Mode
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# Sample GSTINs for testing
SAMPLE_GSTINS = [
    "27AAPFU0939F1ZV",  # Uber India
    "29AABCT1332L1ZN",  # TCS
    "27AADCI7885M1ZJ",  # Reliance Retail
]
