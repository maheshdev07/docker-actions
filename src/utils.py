"""
Utility functions for docker-actions scraper
"""
import os
import json
import time
import random
from datetime import datetime
from pathlib import Path
import pandas as pd
from loguru import logger
from fake_useragent import UserAgent

from src.config import (
    DATA_DIR,
    LOGS_DIR,
    LOG_LEVEL,
    LOG_ROTATION,
    LOG_RETENTION,
    USER_AGENT_ROTATION
)

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    LOGS_DIR / "scraper_{time:YYYY-MM-DD}.log",
    rotation=LOG_ROTATION,
    retention=LOG_RETENTION,
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)
logger.add(
    lambda msg: print(msg, end=""),
    level=LOG_LEVEL,
    format="{time:HH:mm:ss} | {level: <8} | {message}"
)

def get_random_user_agent():
    """
    Generate random user agent string
    
    Returns:
        str: Random user agent
    """
    if not USER_AGENT_ROTATION:
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    try:
        ua = UserAgent()
        return ua.random
    except Exception as e:
        logger.warning(f"Failed to generate random user agent: {e}")
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def get_headers():
    """
    Get HTTP request headers
    
    Returns:
        dict: HTTP headers
    """
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }

def random_delay(min_seconds=1, max_seconds=3):
    """
    Add random delay to mimic human behavior
    
    Args:
        min_seconds (int): Minimum delay in seconds
        max_seconds (int): Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Waiting {delay:.2f} seconds...")
    time.sleep(delay)

def validate_gstin(gstin):
    """
    Validate GSTIN format

    Format: 2 digits + 5 letters + 4 digits + 1 letter + 1 alphanumeric + 1 alphanumeric
    Example: 27AAPFU0939F1ZV

    Args:
        gstin (str): GSTIN to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not gstin or not isinstance(gstin, str):
        return False

    if len(gstin) != 15:
        return False

    import re
    # Standard GSTIN pattern: 2 digits + 5 letters + 4 digits + 1 letter + 3 alphanumeric
    # GSTIN is 15 characters: XXAAAAA9999A999 where X=digit, A=letter, 9=alphanum
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{3}$'
    return bool(re.fullmatch(pattern, gstin.upper()))

def get_timestamp(format_str="%Y%m%d_%H%M%S"):
    """
    Get current timestamp
    
    Args:
        format_str (str): Datetime format string
    
    Returns:
        str: Formatted timestamp
    """
    return datetime.now().strftime(format_str)

def save_to_csv(data, filename=None):
    """
    Save data to CSV file
    
    Args:
        data (list): List of dictionaries
        filename (str): Output filename (optional)
    
    Returns:
        Path: Path to saved file
    """
    if not data:
        logger.warning("No data to save to CSV")
        return None
    
    if filename is None:
        filename = f"gst_data_{get_timestamp()}.csv"
    
    filepath = DATA_DIR / filename
    
    try:
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.success(f"✅ Data saved to CSV: {filepath}")
        logger.info(f"   Records: {len(data)}, Size: {filepath.stat().st_size / 1024:.2f} KB")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")
        return None

def save_to_json(data, filename=None):
    """
    Save data to JSON file
    
    Args:
        data (list): List of dictionaries
        filename (str): Output filename (optional)
    
    Returns:
        Path: Path to saved file
    """
    if not data:
        logger.warning("No data to save to JSON")
        return None
    
    if filename is None:
        filename = f"gst_data_{get_timestamp()}.json"
    
    filepath = DATA_DIR / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.success(f"✅ Data saved to JSON: {filepath}")
        logger.info(f"   Records: {len(data)}, Size: {filepath.stat().st_size / 1024:.2f} KB")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        return None

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           🐳 DOCKER-ACTIONS GST SCRAPER 🐳              ║
    ║                                                          ║
    ║  Automated GST Portal Data Extraction                    ║
    ║  with Docker & GitHub Actions                            ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_summary(data, csv_file=None, json_file=None):
    """
    Print scraping summary
    
    Args:
        data (list): Scraped data
        csv_file (Path): CSV file path
        json_file (Path): JSON file path
    """
    summary = f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                  SCRAPING SUMMARY                        ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Records Scraped:  {len(data):<40} ║
    ║  Timestamp:        {get_timestamp('%Y-%m-%d %H:%M:%S'):<40} ║
    """
    
    if csv_file:
        summary += f"║  CSV Output:       {csv_file.name:<40} ║\n"
    if json_file:
        summary += f"║  JSON Output:      {json_file.name:<40} ║\n"
    
    summary += "╚══════════════════════════════════════════════════════════╝"
    
    print(summary)
