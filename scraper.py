import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
import json
import time
from typing import Optional, Dict, Any, Union, List
import logging
from urllib.parse import urlparse, urljoin
import traceback
import platform
import os
from datetime import datetime

class ScraperError(Exception):
    """Base exception for scraper errors"""
    pass

class AuthenticationError(ScraperError):
    """Raised when authentication fails"""
    pass

class ScrapingError(ScraperError):
    """Raised when scraping fails"""
    pass

class SelectorError(ScraperError):
    """Raised when selector is invalid or no elements found"""
    pass

class SeleniumError(ScraperError):
    """Raised when Selenium operations fail"""
    pass

class WebScraper:
    def __init__(self, use_selenium: bool = False, debug: bool = False):
        """
        Initialize the WebScraper with optional Selenium support.
        
        Args:
            use_selenium (bool): Whether to use Selenium for JavaScript-heavy sites
            debug (bool): Enable debug mode for detailed logging
            
        Raises:
            SeleniumError: If Selenium setup fails
        """
        self.session = requests.Session()
        self.ua = UserAgent()
        self.use_selenium = use_selenium
        self.driver = None
        self.debug = debug
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
        
        if use_selenium:
            self._setup_selenium()

    def _setup_selenium(self):
        """
        Set up Selenium WebDriver with appropriate options
        
        Raises:
            SeleniumError: If WebDriver setup fails
        """
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            if platform.system() == 'Darwin' and platform.machine() == 'arm64':
                # For Mac ARM64, we need to use a specific ChromeDriver
                service = Service()
                self.driver = webdriver.Chrome(options=chrome_options)
            else:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.logger.debug("Selenium WebDriver setup successful")
        except Exception as e:
            error_msg = f"Failed to setup Selenium: {str(e)}"
            self.logger.error(error_msg)
            self.logger.debug(traceback.format_exc())
            raise SeleniumError(error_msg)

    def authenticate(self, url: str, auth_type: str, credentials: Dict[str, str]) -> bool:
        """
        Authenticate with a website.
        
        Args:
            url (str): The login URL
            auth_type (str): Type of authentication ('basic', 'form', or 'api')
            credentials (dict): Authentication credentials
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            self.logger.debug(f'Attempting {auth_type} authentication for {url}')
            
            if auth_type == 'basic':
                self.session.auth = (credentials.get('username'), credentials.get('password'))
                response = self.session.get(url)
                success = response.status_code == 200
                self.logger.debug(f'Basic auth result: {success}')
                return success
                
            elif auth_type == 'form':
                if self.use_selenium:
                    return self._selenium_form_auth(url, credentials)
                else:
                    return self._requests_form_auth(url, credentials)
                    
            elif auth_type == 'api':
                return self._api_auth(url, credentials)
                
            else:
                self.logger.error(f"Unsupported authentication type: {auth_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return False

    def _selenium_form_auth(self, url: str, credentials: Dict[str, str]) -> bool:
        """Handle form-based authentication using Selenium."""
        try:
            self.logger.debug('Starting Selenium form authentication')
            self.driver.get(url)
            
            # Wait for page load
            time.sleep(2)
            
            # Find and fill username field
            username_field = self.driver.find_element('name', credentials.get('username_field', 'username'))
            username_field.send_keys(credentials['username'])
            self.logger.debug('Username field filled')
            
            # Find and fill password field
            password_field = self.driver.find_element('name', credentials.get('password_field', 'password'))
            password_field.send_keys(credentials['password'])
            self.logger.debug('Password field filled')
            
            # Find and click submit button
            submit_button = self.driver.find_element('css selector', credentials.get('submit_selector', 'button[type="submit"]'))
            submit_button.click()
            self.logger.debug('Submit button clicked')
            
            # Wait for login to complete
            time.sleep(2)
            
            # Check if login was successful
            success = 'login' not in self.driver.current_url.lower()
            self.logger.debug(f'Selenium form auth result: {success}')
            return success
            
        except Exception as e:
            self.logger.error(f"Selenium authentication failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return False

    def _requests_form_auth(self, url: str, credentials: Dict[str, str]) -> bool:
        """Handle form-based authentication using requests."""
        try:
            self.logger.debug('Starting requests form authentication')
            # First get the login page to obtain any necessary tokens
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Prepare login data
            login_data = {
                credentials.get('username_field', 'username'): credentials['username'],
                credentials.get('password_field', 'password'): credentials['password']
            }
            
            # Add any additional form fields if needed
            if 'additional_fields' in credentials:
                login_data.update(credentials['additional_fields'])
            
            self.logger.debug('Submitting login form')
            # Submit the login form
            response = self.session.post(url, data=login_data)
            success = response.status_code == 200
            self.logger.debug(f'Requests form auth result: {success}')
            return success
            
        except Exception as e:
            self.logger.error(f"Requests authentication failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return False

    def _api_auth(self, url: str, credentials: Dict[str, str]) -> bool:
        """Handle API-based authentication."""
        try:
            self.logger.debug('Starting API authentication')
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': self.ua.random
            }
            
            response = self.session.post(
                url,
                json=credentials,
                headers=headers
            )
            
            if response.status_code == 200:
                # Store the token if provided
                if 'token' in response.json():
                    self.session.headers.update({
                        'Authorization': f"Bearer {response.json()['token']}"
                    })
                self.logger.debug('API authentication successful')
                return True
            self.logger.debug('API authentication failed')
            return False
            
        except Exception as e:
            self.logger.error(f"API authentication failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return False

    def scrape(self, url: str, parser: str = 'html.parser', wait_time: int = 0) -> BeautifulSoup:
        """
        Scrape content from a URL.
        
        Args:
            url (str): The URL to scrape
            parser (str): The parser to use for BeautifulSoup
            wait_time (int): Time to wait after page load (for dynamic content)
            
        Returns:
            BeautifulSoup object
            
        Raises:
            ScrapingError: If scraping fails
            ValueError: If URL is invalid
        """
        try:
            self.logger.debug(f'Starting to scrape {url}')
            
            if not url:
                raise ValueError("URL cannot be empty")
            
            if self.use_selenium:
                try:
                    self.driver.get(url)
                    if wait_time > 0:
                        self.logger.debug(f'Waiting {wait_time} seconds for dynamic content')
                        time.sleep(wait_time)
                    html = self.driver.page_source
                except WebDriverException as e:
                    raise ScrapingError(f"Selenium error: {str(e)}")
            else:
                try:
                    headers = {'User-Agent': self.ua.random}
                    response = self.session.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    html = response.text
                except requests.exceptions.Timeout:
                    raise ScrapingError(f"Request timed out after 30 seconds")
                except requests.exceptions.ConnectionError as e:
                    raise ScrapingError(f"Failed to connect to {url}: {str(e)}")
                except requests.exceptions.HTTPError as e:
                    raise ScrapingError(f"HTTP error: {str(e)}")
            
            self.logger.debug('Page content retrieved successfully')
            return BeautifulSoup(html, parser)
            
        except Exception as e:
            if not isinstance(e, ScrapingError):
                raise ScrapingError(f"Scraping failed for {url}: {str(e)}")
            raise

    def extract_data(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract data from BeautifulSoup object using CSS selectors.
        
        Args:
            soup (BeautifulSoup): The BeautifulSoup object
            selectors (dict): Dictionary of data keys and their CSS selectors
            
        Returns:
            dict: Extracted data
            
        Raises:
            SelectorError: If selectors are invalid or no elements found
        """
        if not selectors:
            raise SelectorError("No selectors provided")
            
        data = {}
        for key, selector in selectors.items():
            try:
                self.logger.debug(f'Extracting data for key: {key} with selector: {selector}')
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        data[key] = elements[0].get_text(strip=True)
                    else:
                        data[key] = [elem.get_text(strip=True) for elem in elements]
                    self.logger.debug(f'Successfully extracted data for {key}')
                else:
                    self.logger.warning(f'No elements found for selector: {selector}')
                    data[key] = None
            except Exception as e:
                error_msg = f"Failed to extract {key}: {str(e)}"
                self.logger.error(error_msg)
                self.logger.debug(traceback.format_exc())
                raise SelectorError(error_msg)
        return data

    def save_to_json(self, data: Dict[str, Any], filename: str) -> bool:
        """
        Save scraped data to a JSON file.
        
        Args:
            data (dict): The data to save
            filename (str): The output filename
            
        Returns:
            bool: True if save successful, False otherwise
            
        Raises:
            IOError: If file operations fail
        """
        try:
            self.logger.debug(f'Saving data to {filename}')
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.debug('Data saved successfully')
            return True
        except Exception as e:
            error_msg = f"Failed to save data: {str(e)}"
            self.logger.error(error_msg)
            self.logger.debug(traceback.format_exc())
            raise IOError(error_msg)

    def close(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
            self.session.close()
            self.logger.debug('Resources cleaned up successfully')
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            self.logger.debug(traceback.format_exc())

    def parse_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Parse a sitemap and return a list of URLs.
        
        Args:
            sitemap_url (str): URL of the sitemap
            
        Returns:
            List[str]: List of URLs from the sitemap
        """
        try:
            self.logger.debug(f'Parsing sitemap: {sitemap_url}')
            response = self.session.get(sitemap_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'xml')
            urls = []
            
            # Handle both sitemap index and regular sitemaps
            if soup.find('sitemapindex'):
                # This is a sitemap index
                for sitemap in soup.find_all('loc'):
                    sub_urls = self.parse_sitemap(sitemap.text)
                    urls.extend(sub_urls)
            else:
                # This is a regular sitemap
                for url in soup.find_all('loc'):
                    urls.append(url.text)
            
            self.logger.debug(f'Found {len(urls)} URLs in sitemap')
            return urls
            
        except Exception as e:
            self.logger.error(f"Failed to parse sitemap: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return []

    def crawl_website(self, start_url: str, max_pages: int = 100, same_domain_only: bool = True) -> Dict[str, Any]:
        """
        Crawl a website starting from a URL and discover internal links.
        
        Args:
            start_url (str): The starting URL to crawl
            max_pages (int): Maximum number of pages to crawl
            same_domain_only (bool): Whether to only crawl pages from the same domain
            
        Returns:
            Dict[str, Any]: Dictionary containing crawled pages and their data
        """
        try:
            self.logger.debug(f'Starting website crawl from: {start_url}')
            
            # Parse the start URL to get the base domain
            parsed_start_url = urlparse(start_url)
            base_domain = parsed_start_url.netloc
            
            # Initialize sets to track visited and discovered URLs
            visited_urls = set()
            discovered_urls = set([start_url])
            crawl_data = {}
            
            while discovered_urls and len(visited_urls) < max_pages:
                # Get the next URL to crawl
                current_url = discovered_urls.pop()
                
                if current_url in visited_urls:
                    continue
                
                try:
                    self.logger.debug(f'Crawling: {current_url}')
                    
                    # Scrape the current page
                    soup = self.scrape(current_url)
                    
                    # Extract all links from the page
                    links = soup.find_all('a', href=True)
                    
                    # Process each link
                    for link in links:
                        href = link.get('href')
                        if not href:
                            continue
                            
                        # Convert relative URLs to absolute
                        absolute_url = urljoin(current_url, href)
                        parsed_url = urlparse(absolute_url)
                        
                        # Skip if not same domain and same_domain_only is True
                        if same_domain_only and parsed_url.netloc != base_domain:
                            continue
                            
                        # Skip if not http/https
                        if parsed_url.scheme not in ['http', 'https']:
                            continue
                            
                        # Add to discovered URLs if not visited
                        if absolute_url not in visited_urls:
                            discovered_urls.add(absolute_url)
                    
                    # Store the page data
                    crawl_data[current_url] = {
                        'title': soup.title.string if soup.title else None,
                        'links': list(discovered_urls),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Mark as visited
                    visited_urls.add(current_url)
                    
                    # Add a small delay between requests
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Failed to crawl {current_url}: {str(e)}")
                    continue
            
            self.logger.debug(f'Crawl completed. Visited {len(visited_urls)} pages')
            return {
                'base_url': start_url,
                'total_pages': len(visited_urls),
                'pages': crawl_data
            }
            
        except Exception as e:
            self.logger.error(f"Website crawling failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return {}

    def crawl_and_scrape(self, start_url: str, selectors: Dict[str, str], 
                        max_pages: int = 100, same_domain_only: bool = True,
                        wait_time: int = 0) -> Dict[str, Any]:
        """
        Crawl a website and scrape data from each page using provided selectors.
        
        Args:
            start_url (str): The starting URL to crawl
            selectors (dict): Dictionary of data keys and their CSS selectors
            max_pages (int): Maximum number of pages to crawl
            same_domain_only (bool): Whether to only crawl pages from the same domain
            wait_time (int): Time to wait after page load
            
        Returns:
            Dict[str, Any]: Combined data from all crawled pages
        """
        try:
            self.logger.debug(f'Starting crawl and scrape from: {start_url}')
            
            # First crawl the website to discover URLs
            crawl_result = self.crawl_website(start_url, max_pages, same_domain_only)
            
            if not crawl_result or not crawl_result.get('pages'):
                self.logger.error('No pages found to scrape')
                return {}
            
            # Scrape data from each discovered page
            scraped_data = {}
            for url in crawl_result['pages'].keys():
                try:
                    self.logger.debug(f'Scraping data from: {url}')
                    soup = self.scrape(url, wait_time=wait_time)
                    if soup:
                        data = self.extract_data(soup, selectors)
                        if data:
                            scraped_data[url] = data
                except Exception as e:
                    self.logger.error(f"Failed to scrape {url}: {str(e)}")
                    continue
                
                # Add a small delay between requests
                time.sleep(1)
            
            self.logger.debug(f'Crawl and scrape completed. Scraped {len(scraped_data)} pages')
            return {
                'crawl_info': crawl_result,
                'scraped_data': scraped_data
            }
            
        except Exception as e:
            self.logger.error(f"Crawl and scrape failed: {str(e)}")
            self.logger.debug(traceback.format_exc())
            return {} 