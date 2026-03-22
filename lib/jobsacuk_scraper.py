"""
Jobs.ac.uk job board scraper
"""
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.base_scraper import BaseScraper
from utils import random_delay, create_job_dict

class JobsAcUkScraper(BaseScraper):
    """Scraper for Jobs.ac.uk job listings (UK Academic Jobs)"""
    
    def __init__(self, keywords: List[str], max_pages: int = 3):
        super().__init__(keywords)
        self.max_pages = max_pages
        self.base_url = "https://www.jobs.ac.uk"
        
    def build_search_url(self, keyword: str, page: int = 0) -> str:
        """Build Jobs.ac.uk search URL"""
        encoded_keyword = quote_plus(keyword)
        # Jobs.ac.uk uses page parameter starting from 1
        page_num = page + 1
        return f"{self.base_url}/search/?keywords={encoded_keyword}&page={page_num}"
    
    def scrape(self) -> List[Dict]:
        """Scrape jobs from Jobs.ac.uk"""
        self.logger.info("Starting Jobs.ac.uk scraper...")
        
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
        
        self.logger.info(f"Jobs.ac.uk scraping completed. Total jobs: {len(self.jobs)}")
        return self.jobs
    
    def _parse_job_listings(self, soup: BeautifulSoup, keyword: str) -> int:
        """Parse job listings from Jobs.ac.uk page"""
        jobs_found = 0
        
        # Jobs.ac.uk typically uses article or div elements for job listings
        job_cards = soup.find_all('li', class_='job-result')
        if not job_cards:
            job_cards = soup.find_all('article', class_='job')
        if not job_cards:
            job_cards = soup.find_all('div', class_='j-search-result')
        
        for card in job_cards:
            try:
                job_data = self._extract_job_data(card)
                if job_data:
                    job_data['source'] = 'Jobs.ac.uk'
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
            title_elem = card.find('h3') or card.find('h2') or card.find('a', class_='job-title')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Company/Institution
            company_elem = card.find('span', class_='employer') or card.find('div', class_='employer')
            if not company_elem:
                company_elem = card.find('span', class_='institution')
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Location
            location_elem = card.find('span', class_='location') or card.find('div', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # URL
            link_elem = card.find('a', href=True)
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                url = href if href.startswith('http') else self.base_url + href
            else:
                url = ""
            
            # Salary
            salary_elem = card.find('span', class_='salary') or card.find('div', class_='salary')
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Description snippet
            description_elem = card.find('p', class_='description') or card.find('div', class_='snippet')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            if title and (company or location):
                return create_job_dict(
                    title=title,
                    company=company if company else "N/A",
                    location=location,
                    url=url,
                    description=description,
                    salary=salary,
                    source="Jobs.ac.uk"
                )
            
        except Exception as e:
            self.logger.debug(f"Error extracting job data: {str(e)}")
        
        return None
