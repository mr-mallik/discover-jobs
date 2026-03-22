"""
Base scraper class for job boards
"""
from abc import ABC, abstractmethod
from typing import List, Dict
import cloudscraper
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_random_user_agent, random_delay, get_logger

class BaseScraper(ABC):
    """Base class for all job board scrapers"""
    
    def __init__(self, keywords: List[str]):
        self.keywords = keywords
        self.jobs = []
        self.logger = get_logger(self.__class__.__name__)
        self.scraper = self._create_cloudscraper()
        
    def _create_cloudscraper(self):
        """Create a cloudscraper session that can bypass cloudflare"""
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        scraper.headers.update({
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        return scraper
    
    def _create_selenium_driver(self, headless: bool = True):
        """Create a Selenium WebDriver for JavaScript-heavy sites"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    @abstractmethod
    def scrape(self) -> List[Dict]:
        """Main scraping method to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def build_search_url(self, keyword: str, page: int = 0) -> str:
        """Build search URL for a specific keyword and page"""
        pass
    
    def get_jobs(self) -> List[Dict]:
        """Return collected jobs"""
        return self.jobs
    
    def scrape_with_retry(self, max_retries: int = 3) -> List[Dict]:
        """Scrape with retry logic"""
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1} of {max_retries}")
                return self.scrape()
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    random_delay(5, 10)
                else:
                    self.logger.error(f"All {max_retries} attempts failed")
                    return []
