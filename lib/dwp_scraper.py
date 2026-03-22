"""
DWP (Department for Work and Pensions) Find a Job scraper
"""
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.base_scraper import BaseScraper
from utils import random_delay, create_job_dict

class DWPScraper(BaseScraper):
    """Scraper for DWP Find a Job listings (UK Government)"""
    
    def __init__(self, keywords: List[str], max_pages: int = 3):
        super().__init__(keywords)
        self.max_pages = max_pages
        self.base_url = "https://findajob.dwp.gov.uk"
        
    def build_search_url(self, keyword: str, page: int = 0) -> str:
        """Build DWP Find a Job search URL"""
        encoded_keyword = quote_plus(keyword)
        # DWP uses page parameter (0-indexed)
        return f"{self.base_url}/search?q={encoded_keyword}&page={page}"
    
    def scrape(self) -> List[Dict]:
        """Scrape jobs from DWP Find a Job"""
        self.logger.info("Starting DWP Find a Job scraper...")
        
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
        
        self.logger.info(f"DWP Find a Job scraping completed. Total jobs: {len(self.jobs)}")
        return self.jobs
    
    def _parse_job_listings(self, soup: BeautifulSoup, keyword: str) -> int:
        """Parse job listings from DWP page"""
        jobs_found = 0
        
        # DWP typically uses specific class names for job results
        job_cards = soup.find_all('div', class_='search-result')
        if not job_cards:
            job_cards = soup.find_all('article', class_='job')
        if not job_cards:
            # Try finding by data attributes or other selectors
            job_cards = soup.find_all('div', attrs={'data-job-id': True})
        
        for card in job_cards:
            try:
                job_data = self._extract_job_data(card)
                if job_data:
                    job_data['source'] = 'DWP Find a Job'
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
            title_elem = (card.find('h2', class_='govuk-heading-m') or 
                         card.find('h3') or 
                         card.find('a', class_='govuk-link'))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Company/Employer
            company_elem = (card.find('span', class_='company') or 
                           card.find('div', class_='company-name') or
                           card.find('p', class_='govuk-body'))
            company = ""
            if company_elem:
                company_text = company_elem.get_text(strip=True)
                # DWP often includes "at Company Name"
                if company_text.lower().startswith('at '):
                    company = company_text[3:]
                else:
                    company = company_text
            
            # Location
            location_elem = (card.find('span', class_='location') or 
                            card.find('div', class_='location') or
                            card.find('span', class_='govuk-caption-m'))
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
            description_elem = card.find('p', class_='description') or card.find('div', class_='summary')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            if title:
                return create_job_dict(
                    title=title,
                    company=company if company else "N/A",
                    location=location,
                    url=url,
                    description=description,
                    salary=salary,
                    source="DWP Find a Job"
                )
            
        except Exception as e:
            self.logger.debug(f"Error extracting job data: {str(e)}")
        
        return None
