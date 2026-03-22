"""
Job Scraper - Main Script
Scrapes job listings from multiple job boards and saves to JSON
"""
import os
import json
import ast
from datetime import datetime
from dotenv import load_dotenv
from typing import List
from lib.indeed_scraper import IndeedScraper
from lib.linkedin_scraper import LinkedInScraper
from lib.jobsacuk_scraper import JobsAcUkScraper
from lib.dwp_scraper import DWPScraper
from lib.ktp_scraper import KTPScraper
from utils import get_logger
from email_utils import send_job_email

# Load environment variables
load_dotenv()

# Configure logger
logger = get_logger(__name__)

def load_keywords() -> List[str]:
    """Load keywords from environment variable"""
    keywords_str = os.getenv('KEY_WRDS', '[]')
    try:
        # Parse the string representation of list
        keywords = ast.literal_eval(keywords_str)
        if isinstance(keywords, list):
            return keywords
        else:
            logger.warning("KEY_WRDS is not a list, using default keywords")
            return ["Software Engineer", "Python Developer"]
    except Exception as e:
        logger.error(f"Error parsing KEY_WRDS: {str(e)}")
        return ["Software Engineer", "Python Developer"]

def load_locations() -> List[str]:
    """Load locations from environment variable"""
    locations_str = os.getenv('LOCATION', '[]')
    try:
        # Parse the string representation of list
        locations = ast.literal_eval(locations_str)
        if isinstance(locations, list):
            return locations
        else:
            logger.warning("LOCATION is not a list, using default location")
            return ["United Kingdom"]
    except Exception as e:
        logger.error(f"Error parsing LOCATION: {str(e)}")
        return ["United Kingdom"]

def load_job_discovery_limit() -> int:
    """Load job discovery limit from environment variable"""
    limit_str = os.getenv('JOB_DISCOVERY_LIMIT', '0')
    try:
        limit = int(limit_str)
        return limit if limit >= 0 else 0
    except Exception as e:
        logger.error(f"Error parsing JOB_DISCOVERY_LIMIT: {str(e)}")
        return 0  # 0 means unlimited

def save_jobs_to_json(jobs: List[dict], filename: str = None):
    """Save job listings to JSON file in data directory with timestamp"""
    try:
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Generate filename with timestamp if not provided
        if filename is None:
            now = datetime.now()
            filename = f"data/discovered_{now.strftime('%Y_%m_%d')}.json"
        elif not filename.startswith('data/'):
            filename = f"data/{filename}"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved {len(jobs)} jobs to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving jobs to JSON: {str(e)}")
        return None

def remove_duplicates(jobs: List[dict]) -> List[dict]:
    """Remove duplicate job listings based on URL"""
    seen_urls = set()
    unique_jobs = []
    
    for job in jobs:
        url = job.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_jobs.append(job)
        elif not url:
            # Keep jobs without URLs
            unique_jobs.append(job)
    
    return unique_jobs

def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("Starting Job Scraper Automation")
    logger.info("=" * 60)
    
    # Load keywords and locations
    keywords = load_keywords()
    locations = load_locations()
    job_limit = load_job_discovery_limit()
    
    logger.info(f"Keywords: {keywords}")
    logger.info(f"Locations: {locations}")
    if job_limit > 0:
        logger.info(f"Job Discovery Limit: {job_limit} jobs")
    else:
        logger.info(f"Job Discovery Limit: Unlimited")
    
    all_jobs = []
    
    # Scrape Indeed UK
    # logger.info("\n" + "-" * 60)
    # logger.info("SCRAPING INDEED UK")
    # logger.info("-" * 60)
    # try:
    #     # Reduce pages to avoid being blocked (1-2 pages recommended)
    #     indeed_scraper = IndeedScraper(keywords=keywords, locations=locations, max_pages=2)
    #     indeed_jobs = indeed_scraper.scrape_with_retry(max_retries=2)
    #     all_jobs.extend(indeed_jobs)
    #     logger.info(f"Indeed UK: {len(indeed_jobs)} jobs collected")
    #     logger.info(f"Total jobs so far: {len(all_jobs)}")
    # except Exception as e:
    #     logger.error(f"Indeed scraper failed: {str(e)}")
    
    # Scrape LinkedIn
    logger.info("\n" + "-" * 60)
    logger.info("SCRAPING LINKEDIN")
    logger.info("-" * 60)
    try:
        linkedin_scraper = LinkedInScraper(keywords=keywords, locations=locations, max_pages=2)
        linkedin_jobs = linkedin_scraper.scrape_with_retry(max_retries=2)
        all_jobs.extend(linkedin_jobs)
        logger.info(f"LinkedIn: {len(linkedin_jobs)} jobs collected")
        logger.info(f"Total jobs so far: {len(all_jobs)}")
    except Exception as e:
        logger.error(f"LinkedIn scraper failed: {str(e)}")
    
    # Scrape Jobs.ac.uk
    logger.info("\n" + "-" * 60)
    logger.info("SCRAPING JOBS.AC.UK")
    logger.info("-" * 60)
    try:
        jobsacuk_scraper = JobsAcUkScraper(keywords=keywords, max_pages=3)
        jobsacuk_jobs = jobsacuk_scraper.scrape_with_retry(max_retries=3)
        all_jobs.extend(jobsacuk_jobs)
        logger.info(f"Jobs.ac.uk: {len(jobsacuk_jobs)} jobs collected")
    except Exception as e:
        logger.error(f"Jobs.ac.uk scraper failed: {str(e)}")
    
    # Scrape DWP Find a Job
    logger.info("\n" + "-" * 60)
    logger.info("SCRAPING DWP FIND A JOB")
    logger.info("-" * 60)
    try:
        dwp_scraper = DWPScraper(keywords=keywords, max_pages=3)
        dwp_jobs = dwp_scraper.scrape_with_retry(max_retries=3)
        all_jobs.extend(dwp_jobs)
        logger.info(f"DWP Find a Job: {len(dwp_jobs)} jobs collected")
    except Exception as e:
        logger.error(f"DWP scraper failed: {str(e)}")
    
    # Scrape KTP Jobs
    logger.info("\n" + "-" * 60)
    logger.info("SCRAPING KTP JOBS")
    logger.info("-" * 60)
    try:
        ktp_scraper = KTPScraper(keywords=keywords, max_pages=2)
        ktp_jobs = ktp_scraper.scrape_with_retry(max_retries=3)
        all_jobs.extend(ktp_jobs)
        logger.info(f"KTP Jobs: {len(ktp_jobs)} jobs collected")
    except Exception as e:
        logger.error(f"KTP scraper failed: {str(e)}")
    
    # Remove duplicates
    unique_jobs = remove_duplicates(all_jobs)
    logger.info(f"\nTotal jobs collected: {len(all_jobs)}")
    logger.info(f"Unique jobs after deduplication: {len(unique_jobs)}")
    
    # Save to JSON with timestamp
    output_file = save_jobs_to_json(unique_jobs)
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total unique jobs saved: {len(unique_jobs)}")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 60)
    
    # Send email notification
    if unique_jobs:
        logger.info("\n" + "-" * 60)
        logger.info("SENDING EMAIL NOTIFICATION")
        logger.info("-" * 60)
        email_sent = send_job_email(unique_jobs, keywords, locations)
        if email_sent:
            logger.info("✅ Email notification sent successfully")
        else:
            logger.warning("⚠️ Failed to send email notification")
    
    # Print sample of results
    if unique_jobs:
        logger.info("\nSample job (first result):")
        sample = unique_jobs[0]
        logger.info(f"  Title: {sample.get('title', 'N/A')}")
        logger.info(f"  Company: {sample.get('company', 'N/A')}")
        logger.info(f"  Location: {sample.get('location', 'N/A')}")
        logger.info(f"  Source: {sample.get('source', 'N/A')}")
        logger.info(f"  URL: {sample.get('url', 'N/A')}")

if __name__ == "__main__":
    main()
