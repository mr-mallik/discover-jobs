"""
LinkedIn job board scraper
Uses Selenium to handle JavaScript-rendered content
"""
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote_plus
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.base_scraper import BaseScraper
from utils import random_delay, create_job_dict

class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job listings (without login requirement)"""
    
    def __init__(self, keywords: List[str], locations: List[str] = None, max_pages: int = 2):
        super().__init__(keywords)
        self.max_pages = max_pages
        self.base_url = "https://www.linkedin.com"
        self.driver = None
        self.locations = locations if locations else ["United Kingdom"]
        
    def build_search_url(self, keyword: str, location: str = "", page: int = 0) -> str:
        """Build LinkedIn search URL for guest access with location"""
        encoded_keyword = quote_plus(keyword)
        start = page * 25  # LinkedIn shows 25 jobs per page
        
        if location:
            encoded_location = quote_plus(location)
            return f"{self.base_url}/jobs/search?keywords={encoded_keyword}&location={encoded_location}&start={start}"
        else:
            return f"{self.base_url}/jobs/search?keywords={encoded_keyword}&start={start}"
    
    def scrape(self) -> List[Dict]:
        """Scrape jobs from LinkedIn using Selenium"""
        self.logger.info("Starting LinkedIn scraper...")
        
        try:
            # Initialize Selenium driver
            self.driver = self._create_selenium_driver(headless=True)
            self.driver.set_page_load_timeout(30)
            
            for keyword in self.keywords:
                for location in self.locations:
                    self.logger.info(f"Searching for: {keyword} in {location}")
                    
                    for page in range(self.max_pages):
                        try:
                            url = self.build_search_url(keyword, location, page)
                            self.logger.info(f"Scraping page {page + 1}: {url}")
                            
                            self.driver.get(url)
                            
                            # Wait for job listings to load
                            WebDriverWait(self.driver, 15).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "base-search-card"))
                            )
                            
                            # Scroll to load more content
                            self._scroll_page()
                            
                            jobs_found = self._parse_job_listings(keyword)
                            self.logger.info(f"Found {jobs_found} jobs on page {page + 1}")
                            
                            # Be respectful with rate limiting
                            random_delay(4, 7)
                            
                        except TimeoutException:
                            self.logger.warning(f"Timeout loading page {page + 1} for '{keyword}' in '{location}'")
                            continue
                        except Exception as e:
                            self.logger.error(f"Error scraping page {page + 1} for '{keyword}' in '{location}': {str(e)}")
                            continue
            
            self.logger.info(f"LinkedIn scraping completed. Total jobs: {len(self.jobs)}")
            
        except Exception as e:
            self.logger.error(f"Fatal error in LinkedIn scraper: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.jobs
    
    def _scroll_page(self):
        """Scroll the page to load dynamic content"""
        try:
            # Scroll down in increments
            for i in range(3):
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)
        except Exception as e:
            self.logger.debug(f"Error scrolling page: {str(e)}")
    
    def _parse_job_listings(self, keyword: str) -> int:
        """Parse job listings from LinkedIn page"""
        jobs_found = 0
        
        try:
            # Find all job cards
            job_cards = self.driver.find_elements(By.CLASS_NAME, "base-search-card")
            
            for card in job_cards:
                try:
                    job_data = self._extract_job_data(card)
                    if job_data:
                        job_data['source'] = 'LinkedIn'
                        self.jobs.append(job_data)
                        jobs_found += 1
                except Exception as e:
                    self.logger.debug(f"Error parsing job card: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error finding job cards: {str(e)}")
        
        return jobs_found
    
    def _extract_job_data(self, card) -> Dict:
        """Extract job data from a LinkedIn job card"""
        try:
            # Title
            title = ""
            try:
                title_elem = card.find_element(By.CLASS_NAME, "base-search-card__title")
                title = title_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Company
            company = ""
            try:
                company_elem = card.find_element(By.CLASS_NAME, "base-search-card__subtitle")
                company = company_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Location
            location = ""
            try:
                location_elem = card.find_element(By.CLASS_NAME, "job-search-card__location")
                location = location_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # URL
            url = ""
            try:
                link_elem = card.find_element(By.CLASS_NAME, "base-card__full-link")
                url = link_elem.get_attribute("href")
            except NoSuchElementException:
                pass
            
            # Description (LinkedIn doesn't show much in listing view)
            description = ""
            try:
                desc_elem = card.find_element(By.CLASS_NAME, "base-search-card__snippet")
                description = desc_elem.text.strip()
            except NoSuchElementException:
                pass
            
            if title and company:
                return create_job_dict(
                    title=title,
                    company=company,
                    location=location,
                    url=url,
                    description=description,
                    salary="",  # LinkedIn rarely shows salary in listings
                    source="LinkedIn"
                )
            
        except Exception as e:
            self.logger.debug(f"Error extracting job data: {str(e)}")
        
        return None
