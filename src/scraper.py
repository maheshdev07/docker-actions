"""
GST Portal Scraper
Scrapes GST taxpayer information from public GST portal
"""
import sys
import requests
from bs4 import BeautifulSoup
from loguru import logger
import pandas as pd

from config import *
from utils import (
    get_headers, 
    random_delay, 
    save_to_csv, 
    save_to_json,
    validate_gstin,
    get_timestamp,
    create_directories
)

class GSTScraper:
    """GST Portal Web Scraper"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        create_directories()
        logger.info("GST Scraper initialized")
    
    def search_gstin(self, gstin):
        """
        Search for GSTIN details on GST portal
        
        Args:
            gstin (str): 15-digit GSTIN
        
        Returns:
            dict: Taxpayer information
        """
        if not validate_gstin(gstin):
            logger.error(f"Invalid GSTIN format: {gstin}")
            return None
        
        logger.info(f"Searching for GSTIN: {gstin}")
        
        try:
            # Note: This is a simplified example. Real GST portal requires captcha solving
            # For demonstration, we'll scrape the public search page structure
            
            url = f"{GST_SEARCH_URL}?gstin={gstin}"
            
            response = self.session.get(
                url, 
                timeout=TIMEOUT,
                headers=get_headers()
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract data (structure depends on actual GST portal HTML)
            data = {
                'gstin': gstin,
                'legal_name': self._extract_field(soup, 'lgnm'),
                'trade_name': self._extract_field(soup, 'tradeNam'),
                'registration_date': self._extract_field(soup, 'rgdt'),
                'taxpayer_type': self._extract_field(soup, 'dty'),
                'status': self._extract_field(soup, 'sts'),
                'state': self._extract_field(soup, 'stj'),
                'scraped_at': get_timestamp()
            }
            
            logger.info(f"Successfully scraped data for {gstin}")
            random_delay(DELAY_BETWEEN_REQUESTS, DELAY_BETWEEN_REQUESTS + 1)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {gstin}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {gstin}: {str(e)}")
            return None
    
    def _extract_field(self, soup, field_id):
        """Extract field value from HTML"""
        try:
            element = soup.find(id=field_id)
            return element.text.strip() if element else "N/A"
        except:
            return "N/A"
    
    def search_multiple_gstins(self, gstin_list):
        """
        Search for multiple GSTINs
        
        Args:
            gstin_list (list): List of GSTINs
        
        Returns:
            list: List of taxpayer information dictionaries
        """
        results = []
        
        for i, gstin in enumerate(gstin_list, 1):
            logger.info(f"Processing {i}/{len(gstin_list)}: {gstin}")
            
            data = self.search_gstin(gstin)
            if data:
                results.append(data)
            
            # Add delay between requests
            if i < len(gstin_list):
                random_delay(DELAY_BETWEEN_REQUESTS, DELAY_BETWEEN_REQUESTS + 2)
        
        logger.info(f"Completed scraping {len(results)} out of {len(gstin_list)} GSTINs")
        return results
    
    def scrape_sample_data(self):
        """
        Scrape sample GST data for demonstration
        This method simulates scraping when actual portal access is limited
        """
        logger.info("Generating sample GST data for demonstration")
        
        sample_data = [
            {
                'gstin': '27AAPFU0939F1ZV',
                'legal_name': 'UBER INDIA SYSTEMS PRIVATE LIMITED',
                'trade_name': 'UBER',
                'registration_date': '01/07/2017',
                'taxpayer_type': 'Regular',
                'status': 'Active',
                'state': 'Maharashtra',
                'scraped_at': get_timestamp()
            },
            {
                'gstin': '29AABCT1332L1ZN',
                'legal_name': 'TATA CONSULTANCY SERVICES LIMITED',
                'trade_name': 'TCS',
                'registration_date': '01/07/2017',
                'taxpayer_type': 'Regular',
                'status': 'Active',
                'state': 'Karnataka',
                'scraped_at': get_timestamp()
            },
            {
                'gstin': '27AADCI7885M1ZJ',
                'legal_name': 'RELIANCE RETAIL LIMITED',
                'trade_name': 'Reliance Retail',
                'registration_date': '01/07/2017',
                'taxpayer_type': 'Regular',
                'status': 'Active',
                'state': 'Maharashtra',
                'scraped_at': get_timestamp()
            }
        ]
        
        return sample_data
    
    def save_results(self, data, format='csv'):
        """
        Save scraped data to file
        
        Args:
            data (list): List of dictionaries containing scraped data
            format (str): Output format ('csv' or 'json')
        
        Returns:
            str: Path to saved file
        """
        if not data:
            logger.warning("No data to save")
            return None
        
        timestamp = get_timestamp()
        filename = f"gst_data_{timestamp}"
        
        if format == 'csv':
            return save_to_csv(data, f"{filename}.csv")
        elif format == 'json':
            return save_to_json(data, f"{filename}.json")
        else:
            logger.error(f"Unsupported format: {format}")
            return None

def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("GST Scraper Started")
    logger.info("=" * 60)
    
    # Initialize scraper
    scraper = GSTScraper()
    
    # Option 1: Scrape sample data (for demonstration)
    logger.info("Running in DEMO mode - generating sample data")
    data = scraper.scrape_sample_data()
    
    # Option 2: Scrape real GSTINs (uncomment to use)
    # gstin_list = [
    #     '27AAPFU0939F1ZV',
    #     '29AABCT1332L1ZN',
    #     '27AADCI7885M1ZJ'
    # ]
    # data = scraper.search_multiple_gstins(gstin_list)
    
    # Save results
    if data:
        csv_file = scraper.save_results(data, format='csv')
        json_file = scraper.save_results(data, format='json')
        
        logger.success(f"Scraping completed! Saved {len(data)} records")
        logger.success(f"CSV: {csv_file}")
        logger.success(f"JSON: {json_file}")
    else:
        logger.error("No data scraped")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("GST Scraper Finished")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
