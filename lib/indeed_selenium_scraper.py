"""
Alternative Indeed scraper using Selenium for bypassing stricter anti-bot measures
Use this if the regular Indeed scraper keeps getting 403 errors
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

class IndeedSeleniumScraper(BaseScraper):
    """Alternative Selenium-based scraper for Indeed UK (for when cloudflare blocks requests)"""
    
    def __init__(self, keywords: List[str], locations: List[str] = None, max_pages: int = 2):
        super().__init__(keywords)
        self.max_pages = max_pages
        self.base_url = "https://uk.indeed.com"
        self.locations = locations if locations else ["United Kingdom"]
        self.driver = None
        
    def build_search_url(self, keyword: str, location: str = "", page: int = 0) -> str:
        """Build Indeed search URL with location"""
        encoded_keyword = quote_plus(keyword)
        start = page * 10  # Indeed uses 'start' parameter for pagination
        
        if location:
            encoded_location = quote_plus(location)
            return f"{self.base_url}/jobs?q={encoded_keyword}&l={encoded_location}&start={start}"
        else:
            return f"{self.base_url}/jobs?q={encoded_keyword}&start={start}"
    
    def scrape(self) -> List[Dict]:
        """Scrape jobs from Indeed using Selenium"""
        self.logger.info("Starting Indeed Selenium scraper...")
        
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
                            
                            # Wait for job cards to load
                            time.sleep(3)  # Give page time to load
                            
                            jobs_found = self._parse_job_listings()
                            self.logger.info(f"Found {jobs_found} jobs on page {page + 1}")
                            
                            # Longer delays to avoid detection
                            random_delay(6, 10)
                            
                        except TimeoutException:
                            self.logger.warning(f"Timeout loading page {page + 1} for '{keyword}' in '{location}'")
                            continue
                        except Exception as e:
                            self.logger.error(f"Error scraping page {page + 1} for '{keyword}' in '{location}': {str(e)}")
                            continue
            
            self.logger.info(f"Indeed Selenium scraping completed. Total jobs: {len(self.jobs)}")
            
        except Exception as e:
            self.logger.error(f"Fatal error in Indeed Selenium scraper: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.jobs
    
    def _parse_job_listings(self) -> int:
        """Parse job listings from Indeed page using Selenium"""
        jobs_found = 0
        
        try:
            # Wait a bit for dynamic content
            time.sleep(2)
            
            # Find all job cards - Indeed uses various selectors
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")
            if not job_cards:
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.jobsearch-SerpJobCard")
            if not job_cards:
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div[data-jk]")
            
            for card in job_cards:
                try:
                    job_data = self._extract_job_data(card)
                    if job_data:
                        job_data['source'] = 'Indeed'
                        self.jobs.append(job_data)
                        jobs_found += 1
                except Exception as e:
                    self.logger.debug(f"Error parsing job card: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error finding job cards: {str(e)}")
        
        return jobs_found
    
    def _extract_job_data(self, card) -> Dict:
        """Extract job data from a job card using Selenium"""
        try:
            # Title
            title = ""
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "h2.jobTitle")
                title = title_elem.text.strip()
            except NoSuchElementException:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle")
                    title = title_elem.text.strip()
                except NoSuchElementException:
                    pass
            
            # Company
            company = ""
            try:
                company_elem = card.find_element(By.CSS_SELECTOR, "span.companyName")
                company = company_elem.text.strip()
            except NoSuchElementException:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']")
                    company = company_elem.text.strip()
                except NoSuchElementException:
                    pass
            
            # Location
            location = ""
            try:
                location_elem = card.find_element(By.CSS_SELECTOR, "div.companyLocation")
                location = location_elem.text.strip()
            except NoSuchElementException:
                try:
                    location_elem = card.find_element(By.CSS_SELECTOR, "div[data-testid='text-location']")
                    location = location_elem.text.strip()
                except NoSuchElementException:
                    pass
            
            # URL
            url = ""
            try:
                link_elem = card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle")
                url = link_elem.get_attribute("href")
            except NoSuchElementException:
                job_key = card.get_attribute("data-jk")
                if job_key:
                    url = f"{self.base_url}/viewjob?jk={job_key}"
            
            # Salary
            salary = ""
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, "div.salary-snippet")
                salary = salary_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Description
            description = ""
            try:
                desc_elem = card.find_element(By.CSS_SELECTOR, "div.job-snippet")
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
                    salary=salary,
                    source="Indeed"
                )
            
        except Exception as e:
            self.logger.debug(f"Error extracting job data: {str(e)}")
        
        return None
