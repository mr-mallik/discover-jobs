"""
Utility functions for job scraper
"""
import time
import random
import logging
from fake_useragent import UserAgent
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_random_user_agent() -> str:
    """Generate a random user agent string"""
    try:
        ua = UserAgent()
        return ua.random
    except Exception:
        # Fallback user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        ]
        return random.choice(user_agents)

def random_delay(min_seconds: float = 2, max_seconds: float = 5) -> None:
    """Add a random delay to avoid rate limiting"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def sanitize_text(text: Optional[str]) -> str:
    """Clean and sanitize text content"""
    if not text:
        return ""
    return " ".join(text.strip().split())

def create_job_dict(title: str, company: str, location: str, url: str, 
                    description: str = "", salary: str = "", source: str = "") -> dict:
    """Create a standardized job dictionary"""
    return {
        "title": sanitize_text(title),
        "company": sanitize_text(company),
        "location": sanitize_text(location),
        "url": url,
        "description": sanitize_text(description),
        "salary": sanitize_text(salary),
        "source": source,
        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
