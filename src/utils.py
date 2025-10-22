"""
Utility functions for GST scraper
"""
import os
import json
import time
import random
from datetime import datetime
from loguru import logger
from fake_useragent import UserAgent

# Configure logger
logger.add(
    "logs/scraper_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO"
)

def get_random_user_agent():
    """Generate random user agent"""
    ua = UserAgent()
    return ua.random

def get_headers():
    """Get HTTP headers for requests"""
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def random_delay(min_seconds=1, max_seconds=3):
    """Add random delay to avoid detection"""
    delay = random.uniform(min_seconds, max_seconds)
    logger.info(f"Waiting {delay:.2f} seconds...")
    time.sleep(delay)

def save_to_csv(data, filename):
    """Save data to CSV file"""
    import pandas as pd
    
    filepath = os.path.join("data", filename)
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    logger.info(f"Data saved to {filepath}")
    return filepath

def save_to_json(data, filename):
    """Save data to JSON file"""
    filepath = os.path.join("data", filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Data saved to {filepath}")
    return filepath

def validate_gstin(gstin):
    """Validate GSTIN format"""
    if not gstin or len(gstin) != 15:
        return False
    
    # Basic format: 2 digits + 10 alphanumeric + 1 alphabet + 1 digit + 1 alphabet
    import re
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    return bool(re.match(pattern, gstin))

def get_timestamp():
    """Get current timestamp"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def create_directories():
    """Create necessary directories"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    logger.info("Directories created/verified")
