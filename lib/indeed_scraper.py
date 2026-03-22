"""
Indeed job board scraper
"""
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.base_scraper import BaseScraper
from utils import random_delay, create_job_dict

class IndeedScraper(BaseScraper):
    """Scraper for Indeed UK job listings"""
    
    def __init__(self, keywords: List[str], locations: List[str] = None, max_pages: int = 3):
        super().__init__(keywords)
        self.max_pages = max_pages
        self.base_url = "https://uk.indeed.com"
        self.locations = locations if locations else ["United Kingdom"]
        self._setup_indeed_headers()
        
    def _setup_indeed_headers(self):
        """Setup Indeed-specific headers to avoid 403 errors"""
        # Update scraper with more realistic headers
        self.scraper.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://uk.indeed.com/',
        })
        
        # Initialize session by visiting homepage first
        try:
            self.logger.info("Initializing session with Indeed homepage...")
            self.scraper.get(self.base_url, timeout=15)
            random_delay(2, 4)
        except Exception as e:
            self.logger.warning(f"Could not initialize Indeed session: {str(e)}")
        
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
        """Scrape jobs from Indeed"""
        self.logger.info("Starting Indeed scraper...")
        
        for keyword in self.keywords:
            for location in self.locations:
                self.logger.info(f"Searching for: {keyword} in {location}")
                
                for page in range(self.max_pages):
                    try:
                        url = self.build_search_url(keyword, location, page)
                        self.logger.info(f"Scraping page {page + 1}: {url}")
                        
                        # Add referer for subsequent requests
                        if page > 0:
                            self.scraper.headers['Referer'] = self.build_search_url(keyword, location, page - 1)
                        
                        # Try request with retries for 403 errors
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                response = self.scraper.get(url, timeout=30)
                                response.raise_for_status()
                                break  # Success, exit retry loop
                            except Exception as e:
                                if '403' in str(e) and attempt < max_retries - 1:
                                    wait_time = (attempt + 1) * 5
                                    self.logger.warning(f"Got 403 error, waiting {wait_time}s before retry {attempt + 2}/{max_retries}...")
                                    random_delay(wait_time, wait_time + 3)
                                else:
                                    raise  # Re-raise if not 403 or last attempt
                        
                        soup = BeautifulSoup(response.content, 'html.parser')
                        jobs_found = self._parse_job_listings(soup, keyword)
                        
                        self.logger.info(f"Found {jobs_found} jobs on page {page + 1}")
                        
                        # Longer delays to avoid triggering anti-bot
                        random_delay(5, 9)
                        
                    except Exception as e:
                        self.logger.error(f"Error scraping page {page + 1} for '{keyword}' in '{location}': {str(e)}")
                        # Add extra delay after error
                        random_delay(10, 15)
                        continue
        
        self.logger.info(f"Indeed scraping completed. Total jobs: {len(self.jobs)}")
        return self.jobs
    
    def _parse_job_listings(self, soup: BeautifulSoup, keyword: str) -> int:
        """Parse job listings from Indeed page"""
        jobs_found = 0
        
        # Indeed uses various class names, trying multiple selectors
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        if not job_cards:
            job_cards = soup.find_all('div', class_='jobsearch-SerpJobCard')
        if not job_cards:
            job_cards = soup.find_all('div', {'data-jk': True})
        
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
        
        return jobs_found
    
    def _extract_job_data(self, card) -> Dict:
        """Extract job data from a job card"""
        try:
            # Title
            title_elem = card.find('h2', class_='jobTitle') or card.find('a', class_='jcs-JobTitle')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Company
            company_elem = card.find('span', class_='companyName') or card.find('span', {'data-testid': 'company-name'})
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Location
            location_elem = card.find('div', class_='companyLocation') or card.find('div', {'data-testid': 'text-location'})
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # URL
            link_elem = card.find('a', class_='jcs-JobTitle') or title_elem
            job_key = card.get('data-jk', '')
            if link_elem and link_elem.get('href'):
                url = self.base_url + link_elem['href']
            elif job_key:
                url = f"{self.base_url}/viewjob?jk={job_key}"
            else:
                url = ""
            
            # Salary
            salary_elem = card.find('div', class_='salary-snippet') or card.find('div', {'data-testid': 'attribute_snippet_testid'})
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Description snippet
            description_elem = card.find('div', class_='job-snippet') or card.find('ul')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
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
