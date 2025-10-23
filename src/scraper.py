"""
Main scraper module for docker-actions GST portal scraper
"""
import sys
import requests
from bs4 import BeautifulSoup
from loguru import logger

from src.config import (
    GST_SEARCH_URL,
    GST_TAXPAYER_URL,
    DELAY_BETWEEN_REQUESTS,
    MAX_RETRIES,
    REQUEST_TIMEOUT,  OUTPUT_FORMAT,
    DEMO_MODE,
    SAMPLE_GSTINS
)

from src.utils import (
    get_headers,
    random_delay,
    validate_gstin,
    get_timestamp,
    save_to_csv,
    save_to_json,
    print_banner,
    print_summary
)


class GSTScraper:
    """
    GST Portal Web Scraper
    
    Scrapes taxpayer information from GST portal with retry logic,
    rate limiting, and comprehensive error handling.
    """
    
    def __init__(self):
        """Initialize scraper with requests session"""
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        self.scraped_count = 0
        self.failed_count = 0
        
        logger.info("GST Scraper initialized")
        logger.info(f"Demo mode: {DEMO_MODE}")
        logger.info(f"Max retries: {MAX_RETRIES}")
        logger.info(f"Request timeout: {REQUEST_TIMEOUT}s")
    
    def search_gstin(self, gstin):
        """
        Search for GSTIN details
        
        Args:
            gstin (str): 15-digit GSTIN
        
        Returns:
            dict: Taxpayer information or None if failed
        """
        # Validate GSTIN format
        if not validate_gstin(gstin):
            logger.error(f"❌ Invalid GSTIN format: {gstin}")
            self.failed_count += 1
            return None
        
        logger.info(f"🔍 Searching GSTIN: {gstin}")
        
        # Attempt scraping with retry logic
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Make HTTP request
                response = self.session.get(
                    GST_SEARCH_URL,
                    params={'gstin': gstin},
                    timeout=REQUEST_TIMEOUT,
                    headers=get_headers()
                )
                
                # Check response status
                response.raise_for_status()
                
                # Parse HTML content
                soup = BeautifulSoup(response.content, 'lxml')

                # Extract comprehensive data from GST portal
                data = {
                    'gstin': gstin,
                    'legal_name': self._extract_field(soup, 'legalName') or self._extract_text_by_label(soup, 'Legal Name of Business') or 'N/A',
                    'trade_name': self._extract_field(soup, 'tradeName') or self._extract_text_by_label(soup, 'Trade Name') or 'N/A',
                    'registration_date': self._extract_field(soup, 'registrationDate') or self._extract_text_by_label(soup, 'Effective Date of registration') or 'N/A',
                    'constitution_of_business': self._extract_text_by_label(soup, 'Constitution of Business') or 'N/A',
                    'gstin_status': self._extract_text_by_label(soup, 'GSTIN / UIN Status') or 'Active',
                    'taxpayer_type': self._extract_text_by_label(soup, 'Taxpayer Type') or 'Regular',
                    'state': self._extract_jurisdiction_info(soup, 'State') or 'N/A',
                    'center_jurisdiction': self._extract_jurisdiction_info(soup, 'Center') or 'N/A',
                    'state_jurisdiction': self._extract_jurisdiction_info(soup, 'State') or 'N/A',
                    'principal_place_of_business': self._extract_text_by_label(soup, 'Principal Place of Business') or 'N/A',
                    'aadhaar_authenticated': self._extract_text_by_label(soup, 'Whether Aadhaar Authenticated?') or 'N/A',
                    'e_kyc_verified': self._extract_text_by_label(soup, 'Whether e-KYC Verified?') or 'N/A',
                    'nature_of_core_business_activity': self._extract_text_by_label(soup, 'Nature Of Core Business Activity') or 'N/A',
                    'nature_of_business_activities': self._extract_business_activities(soup) or [],
                    'dealing_in_goods': self._extract_dealing_info(soup, 'Goods') or [],
                    'dealing_in_services': self._extract_dealing_info(soup, 'Services') or [],
                    'gstr3b_filing_details': self._extract_filing_details(soup, 'GSTR3B') or [],
                    'gstr1_itr_filing_details': self._extract_filing_details(soup, 'GSTR-1/IFF') or [],
                    'additional_trade_names': self._extract_additional_trade_names(soup) or [],
                    'scraped_at': get_timestamp('%Y-%m-%d %H:%M:%S'),
                    'scraper_version': '2.0'
                }
                
                logger.success(f"✅ Successfully scraped: {gstin}")
                self.scraped_count += 1
                return data
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏱️  Timeout on attempt {attempt}/{MAX_RETRIES} for {gstin}")
                if attempt < MAX_RETRIES:
                    random_delay(2, 4)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Request failed on attempt {attempt}/{MAX_RETRIES}: {str(e)}")
                if attempt < MAX_RETRIES:
                    random_delay(2, 4)
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error: {str(e)}")
                break
        
        # All retries failed
        logger.error(f"❌ Failed to scrape {gstin} after {MAX_RETRIES} attempts")
        self.failed_count += 1
        return None
    
    def _extract_field(self, soup, field_name):
        """
        Extract field value from HTML soup

        Args:
            soup (BeautifulSoup): Parsed HTML
            field_name (str): Field identifier

        Returns:
            str: Extracted value or None
        """
        try:
            # Try various extraction methods
            element = soup.find(id=field_name)
            if element:
                return element.text.strip()

            element = soup.find('span', {'class': field_name})
            if element:
                return element.text.strip()

            return None
        except Exception:
            return None

    def _extract_text_by_label(self, soup, label_text):
        """
        Extract text following a specific label

        Args:
            soup (BeautifulSoup): Parsed HTML
            label_text (str): Label text to search for

        Returns:
            str: Extracted text or None
        """
        try:
            # Find the label element
            label = soup.find(string=lambda text: text and label_text in text.strip())
            if label:
                # Get the next sibling or parent next sibling
                parent = label.parent
                if parent:
                    # Look for the next element containing the value
                    next_element = parent.find_next_sibling()
                    if next_element:
                        return next_element.get_text(strip=True)

                    # Try finding text in the same parent
                    text_parts = []
                    for element in parent.next_siblings:
                        if element.name and element.get_text(strip=True):
                            text_parts.append(element.get_text(strip=True))
                        elif isinstance(element, str) and element.strip():
                            text_parts.append(element.strip())

                    if text_parts:
                        return ' '.join(text_parts)

            # Alternative: find by pattern in text
            for element in soup.find_all(text=True):
                if label_text in element:
                    parent = element.parent
                    if parent:
                        # Get all text after the label in the same container
                        container = parent.parent if parent.parent else parent
                        texts = container.find_all(text=True)
                        label_index = None
                        for i, text in enumerate(texts):
                            if label_text in text:
                                label_index = i
                                break

                        if label_index is not None and label_index + 1 < len(texts):
                            return texts[label_index + 1].strip()

            return None
        except Exception:
            return None

    def _extract_jurisdiction_info(self, soup, jurisdiction_type):
        """
        Extract jurisdiction information

        Args:
            soup (BeautifulSoup): Parsed HTML
            jurisdiction_type (str): 'Center' or 'State'

        Returns:
            str: Jurisdiction info or None
        """
        try:
            # Look for jurisdiction headers
            headers = soup.find_all(['h3', 'h4', 'strong', 'b'])
            for header in headers:
                header_text = header.get_text(strip=True)
                if jurisdiction_type.upper() in header_text and 'JURISDICTION' in header_text:
                    # Get the next elements
                    container = header.parent
                    info_parts = []

                    # Find subsequent elements until next header
                    current = header
                    while current:
                        current = current.find_next_sibling()
                        if current and current.name in ['div', 'p', 'span']:
                            text = current.get_text(strip=True)
                            if text and not any(word in text.upper() for word in ['CENTER', 'STATE', 'JURISDICTION']):
                                info_parts.append(text)
                        elif current and current.name in ['h3', 'h4', 'strong', 'b']:
                            break

                    return ' '.join(info_parts) if info_parts else None

            return None
        except Exception:
            return None

    def _extract_business_activities(self, soup):
        """
        Extract nature of business activities

        Args:
            soup (BeautifulSoup): Parsed HTML

        Returns:
            list: List of business activities
        """
        try:
            activities = []
            # Look for the business activities section
            section = soup.find(string=lambda text: text and 'Nature of Business Activities' in text)
            if section:
                container = section.parent.parent if section.parent else section.parent
                list_items = container.find_all('li') if container else []

                for item in list_items:
                    text = item.get_text(strip=True)
                    if text:
                        activities.append(text)

            return activities
        except Exception:
            return []

    def _extract_dealing_info(self, soup, category):
        """
        Extract dealing in goods/services information

        Args:
            soup (BeautifulSoup): Parsed HTML
            category (str): 'Goods' or 'Services'

        Returns:
            list: List of HSN/description pairs
        """
        try:
            items = []
            # Find the dealing section
            section_header = soup.find(string=lambda text: text and f'Dealing In {category}' in text)
            if section_header:
                container = section_header.parent
                # Find table or structured data
                table = container.find_next('table')
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    for row in rows:
                        cols = row.find_all(['td', 'th'])
                        if len(cols) >= 2:
                            hsn = cols[0].get_text(strip=True)
                            desc = cols[1].get_text(strip=True)
                            if hsn and desc:
                                items.append({'hsn': hsn, 'description': desc})

            return items
        except Exception:
            return []

    def _extract_filing_details(self, soup, filing_type):
        """
        Extract filing details for GSTR3B or GSTR-1/IFF

        Args:
            soup (BeautifulSoup): Parsed HTML
            filing_type (str): 'GSTR3B' or 'GSTR-1/IFF'

        Returns:
            list: List of filing records
        """
        try:
            filings = []
            # Find the filing section
            section_header = soup.find(string=lambda text: text and f'Filing details for {filing_type}' in text)
            if section_header:
                container = section_header.parent
                table = container.find_next('table')
                if table:
                    rows = table.find_all('tr')[1:]  # Skip header
                    for row in rows:
                        cols = row.find_all(['td', 'th'])
                        if len(cols) >= 3:
                            financial_year = cols[0].get_text(strip=True)
                            period = cols[1].get_text(strip=True)
                            status = cols[2].get_text(strip=True)
                            filings.append({
                                'financial_year': financial_year,
                                'period': period,
                                'status': status
                            })

            return filings
        except Exception:
            return []

    def _extract_additional_trade_names(self, soup):
        """
        Extract additional trade names

        Args:
            soup (BeautifulSoup): Parsed HTML

        Returns:
            list: List of additional trade names
        """
        try:
            names = []
            # Find additional trade names section
            section = soup.find(string=lambda text: text and 'Additional Trade Name' in text)
            if section:
                container = section.parent
                # Look for view link or list
                view_link = container.find('a', string=lambda text: text and 'View' in text)
                if view_link:
                    # This would require JavaScript execution to get full list
                    # For now, just indicate that additional names exist
                    names.append("Additional trade names available (click View to see details)")

            return names
        except Exception:
            return []
    
    def search_multiple_gstins(self, gstin_list):
        """
        Search multiple GSTINs with rate limiting

        Args:
            gstin_list (list): List of GSTINs to scrape

        Returns:
            list: List of scraped data dictionaries
        """
        results = []
        total = len(gstin_list)

        logger.info(f"📋 Starting batch scraping: {total} GSTINs")

        for index, gstin in enumerate(gstin_list, 1):
            logger.info(f"Progress: {index}/{total}")

            data = self.search_gstin(gstin)
            if data:
                results.append(data)

            # Add delay between requests (except last one)
            if index < total:
                random_delay(DELAY_BETWEEN_REQUESTS, DELAY_BETWEEN_REQUESTS + 1)

        logger.info(f"✅ Batch complete: {self.scraped_count} succeeded, {self.failed_count} failed")
        return results

    def scrape_single_gstin(self, gstin):
        """
        Scrape a single GSTIN and return the data

        Args:
            gstin (str): GSTIN to scrape

        Returns:
            dict: Scraped data or None if failed
        """
        logger.info(f"🔍 Scraping single GSTIN: {gstin}")

        # Validate GSTIN first
        if not validate_gstin(gstin):
            logger.error(f"❌ Invalid GSTIN format: {gstin}")
            return None

        if DEMO_MODE:
            # Return demo data for the GSTIN
            demo_data = self.generate_demo_data()
            for item in demo_data:
                if item['gstin'] == gstin:
                    return item
            # If GSTIN not in demo data, return a generated demo item for the GSTIN
            return self._generate_demo_for_gstin(gstin)
        else:
            return self.search_gstin(gstin)

    def _generate_demo_for_gstin(self, gstin):
        """
        Generate demo data for a specific GSTIN

        Args:
            gstin (str): GSTIN to generate demo data for

        Returns:
            dict: Demo data for the GSTIN
        """
        from src.utils import get_timestamp

        # Extract state code from GSTIN (first 2 digits)
        state_code = gstin[:2]

        # Map state codes to state names (simplified)
        state_map = {
            '01': 'Jammu and Kashmir',
            '02': 'Himachal Pradesh',
            '03': 'Punjab',
            '04': 'Chandigarh',
            '05': 'Uttarakhand',
            '06': 'Haryana',
            '07': 'Delhi',
            '08': 'Rajasthan',
            '09': 'Uttar Pradesh',
            '10': 'Bihar',
            '11': 'Sikkim',
            '12': 'Arunachal Pradesh',
            '13': 'Nagaland',
            '14': 'Manipur',
            '15': 'Mizoram',
            '16': 'Tripura',
            '17': 'Meghalaya',
            '18': 'Assam',
            '19': 'West Bengal',
            '20': 'Jharkhand',
            '21': 'Odisha',
            '22': 'Chhattisgarh',
            '23': 'Madhya Pradesh',
            '24': 'Gujarat',
            '25': 'Daman and Diu',
            '26': 'Dadra and Nagar Haveli',
            '27': 'Maharashtra',
            '28': 'Andhra Pradesh',
            '29': 'Karnataka',
            '30': 'Goa',
            '31': 'Lakshadweep',
            '32': 'Kerala',
            '33': 'Tamil Nadu',
            '34': 'Puducherry',
            '35': 'Andaman and Nicobar Islands',
            '36': 'Telangana',
            '37': 'Andhra Pradesh (New)',
        }

        state_name = state_map.get(state_code, 'Unknown State')

        return {
            'gstin': gstin,
            'legal_name': f'gstin[2:7]',
            'trade_name': f'gstin[2:7]',
            'registration_date': '01/07/2017',
            'taxpayer_type': 'Regular',
            'status': 'Active',
            'state': state_name,
            'center_jurisdiction': f'{state_name.split()[0]} Central',
            'state_jurisdiction': f'{state_name} State GST',
            'scraped_at': get_timestamp('%Y-%m-%d %H:%M:%S'),
            'scraper_version': '1.0'
        }

    def generate_demo_data(self):
        """
        Generate demo data for testing (when actual scraping is not possible)
        
        Returns:
            list: Demo data
        """
        logger.info("🎭 Running in DEMO mode - generating sample data")
        
        demo_data = [
            {
                'gstin': '27AAPFU0939F1ZV',
                'legal_name': 'UBER INDIA SYSTEMS PRIVATE LIMITED',
                'trade_name': 'UBER',
                'registration_date': '01/07/2017',
                'taxpayer_type': 'Regular',
                'status': 'Active',
                'state': 'Maharashtra',
                'center_jurisdiction': 'Mumbai Central',
                'state_jurisdiction': 'Mumbai State GST',
                'scraped_at': get_timestamp('%Y-%m-%d %H:%M:%S'),
                'scraper_version': '1.0'
            },
            {
                'gstin': '29AABCT1332L1ZN',
                'legal_name': 'TATA CONSULTANCY SERVICES LIMITED',
                'trade_name': 'TCS',
                'registration_date': '01/07/2017',
                'taxpayer_type': 'Regular',
                'status': 'Active',
                'state': 'Karnataka',
                'center_jurisdiction': 'Bangalore Central',
                'state_jurisdiction': 'Karnataka State GST',
                'scraped_at': get_timestamp('%Y-%m-%d %H:%M:%S'),
                'scraper_version': '1.0'
            },
            {
                'gstin': '27AADCI7885M1ZJ',
                'legal_name': 'RELIANCE RETAIL LIMITED',
                'trade_name': 'Reliance Retail',
                'registration_date': '01/07/2017',
                'taxpayer_type': 'Regular',
                'status': 'Active',
                'state': 'Maharashtra',
                'center_jurisdiction': 'Mumbai Central',
                'state_jurisdiction': 'Mumbai State GST',
                'scraped_at': get_timestamp('%Y-%m-%d %H:%M:%S'),
                'scraper_version': '1.0'
            },
            {
                'gstin': '09AAACH7409R1ZN',
                'legal_name': 'HCL TECHNOLOGIES LIMITED',
                'trade_name': 'HCL Tech',
                'registration_date': '01/07/2017',
                'taxpayer_type': 'Regular',
                'status': 'Active',
                'state': 'Uttar Pradesh',
                'center_jurisdiction': 'Noida Central',
                'state_jurisdiction': 'UP State GST',
                'scraped_at': get_timestamp('%Y-%m-%d %H:%M:%S'),
                'scraper_version': '1.0'
            },
            {
                'gstin': '29AAACI1681G1ZU',
                'legal_name': 'INFOSYS LIMITED',
                'trade_name': 'Infosys',
                'registration_date': '01/07/2017',
                'taxpayer_type': 'Regular',
                'status': 'Active',
                'state': 'Karnataka',
                'center_jurisdiction': 'Bangalore Central',
                'state_jurisdiction': 'Karnataka State GST',
                'scraped_at': get_timestamp('%Y-%m-%d %H:%M:%S'),
                'scraper_version': '1.0'
            }
        ]
        
        self.scraped_count = len(demo_data)
        logger.success(f"✅ Generated {len(demo_data)} demo records")
        
        return demo_data
    
    def save_results(self, data):
        """
        Save scraped data to files
        
        Args:
            data (list): List of scraped data dictionaries
        
        Returns:
            tuple: (csv_file_path, json_file_path)
        """
        if not data:
            logger.warning("⚠️  No data to save")
            return None, None
        
        csv_file = None
        json_file = None
        
        # Save based on OUTPUT_FORMAT configuration
        if OUTPUT_FORMAT in ['csv', 'both']:
            csv_file = save_to_csv(data)
        
        if OUTPUT_FORMAT in ['json', 'both']:
            json_file = save_to_json(data)
        
        return csv_file, json_file


def main():
    """Main execution function"""
    try:
        # Print banner
        print_banner()
        
        logger.info("="*60)
        logger.info("🚀 Starting GST Scraper")
        logger.info("="*60)
        
        # Initialize scraper
        scraper = GSTScraper()
        
        # Scrape data
        if DEMO_MODE:
            # Demo mode: Generate sample data
            data = scraper.generate_demo_data()
        else:
            # Real mode: Scrape actual GSTINs
            gstin_list = SAMPLE_GSTINS
            logger.info(f"📝 GSTINs to scrape: {gstin_list}")
            data = scraper.search_multiple_gstins(gstin_list)
        
        # Save results
        if data:
            csv_file, json_file = scraper.save_results(data)
            
            # Print summary
            print_summary(data, csv_file, json_file)
            
            logger.success("🎉 Scraping completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ No data was scraped")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️  Scraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"💥 Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("="*60)
        logger.info("🏁 GST Scraper finished")
        logger.info("="*60)


if __name__ == "__main__":
    main()
