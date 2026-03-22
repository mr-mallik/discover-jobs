"""
KTP (Knowledge Transfer Partnership) Jobs scraper
"""
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.base_scraper import BaseScraper
from utils import random_delay, create_job_dict

class KTPScraper(BaseScraper):
    """Scraper for KTP (Innovate UK) job listings"""
    
    def __init__(self, keywords: List[str], max_pages: int = 2):
        super().__init__(keywords)
        self.max_pages = max_pages
        self.base_url = "https://iuk-ktp.org.uk"
        
    def build_search_url(self, keyword: str, page: int = 0) -> str:
        """Build KTP Jobs search URL"""
        encoded_keyword = quote_plus(keyword)
        # KTP may use different pagination, adjust as needed
        return f"{self.base_url}/jobs/?search={encoded_keyword}&page={page}"
    
    def scrape(self) -> List[Dict]:
        """Scrape jobs from KTP Jobs"""
        self.logger.info("Starting KTP Jobs scraper...")
        
        for keyword in self.keywords:
            self.logger.info(f"Searching for: {keyword}")
            
            for page in range(self.max_pages):
                try:
                    url = self.build_search_url(keyword, page)
                    self.logger.info(f"Scraping page {page + 1}: {url}")
                    
                    response = self.scraper.get(url, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    jobs_found = self._parse_job_listings(soup, keyword)
                    
                    self.logger.info(f"Found {jobs_found} jobs on page {page + 1}")
                    
                    # Be respectful with rate limiting
                    random_delay(3, 6)
                    
                except Exception as e:
                    self.logger.error(f"Error scraping page {page + 1} for '{keyword}': {str(e)}")
                    continue
        
        self.logger.info(f"KTP Jobs scraping completed. Total jobs: {len(self.jobs)}")
        return self.jobs
    
    def _parse_job_listings(self, soup: BeautifulSoup, keyword: str) -> int:
        """Parse job listings from KTP page"""
        jobs_found = 0
        
        # KTP job listing selectors - these may need adjustment based on actual site structure
        job_cards = soup.find_all('div', class_='job-listing')
        if not job_cards:
            job_cards = soup.find_all('article', class_='job')
        if not job_cards:
            job_cards = soup.find_all('div', class_='vacancy')
        if not job_cards:
            # Try finding any divs with job-related classes
            job_cards = soup.find_all('div', class_=lambda x: x and 'job' in x.lower())
        
        for card in job_cards:
            try:
                job_data = self._extract_job_data(card)
                if job_data:
                    job_data['source'] = 'KTP Jobs'
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
            title_elem = (card.find('h2') or 
                         card.find('h3') or 
                         card.find('a', class_='job-title') or
                         card.find('div', class_='title'))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Company/Organisation (KTP is usually partnerships)
            company_elem = (card.find('span', class_='company') or 
                           card.find('div', class_='organisation') or
                           card.find('span', class_='partner'))
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Location
            location_elem = (card.find('span', class_='location') or 
                            card.find('div', class_='location') or
                            card.find('span', class_='region'))
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # URL
            link_elem = card.find('a', href=True)
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                url = href if href.startswith('http') else self.base_url + href
            else:
                url = ""
            
            # Salary (may not be common in KTP listings)
            salary_elem = card.find('span', class_='salary') or card.find('div', class_='salary')
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Description snippet
            description_elem = (card.find('p', class_='description') or 
                               card.find('div', class_='summary') or
                               card.find('p'))
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            if title:
                return create_job_dict(
                    title=title,
                    company=company if company else "N/A",
                    location=location,
                    url=url,
                    description=description,
                    salary=salary,
                    source="KTP Jobs"
                )
            
        except Exception as e:
            self.logger.debug(f"Error extracting job data: {str(e)}")
        
        return None
