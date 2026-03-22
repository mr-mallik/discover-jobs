"""
Email utilities for sending job notifications
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime
from utils import get_logger

logger = get_logger(__name__)

def create_text_email(jobs: List[Dict], keywords: List[str], locations: List[str]) -> str:
    """Create plain text email content from job listings"""
    
    # Group jobs by source
    jobs_by_source = {}
    for job in jobs:
        source = job.get('source', 'Unknown')
        if source not in jobs_by_source:
            jobs_by_source[source] = []
        jobs_by_source[source].append(job)
    
    # Build text email
    text = f"""
JOB DISCOVERY REPORT
{'=' * 60}

Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Keywords: {', '.join(keywords)}
Locations: {', '.join(locations)}

SUMMARY
{'-' * 60}
Total Jobs Found: {len(jobs)}
Job Boards: {len(jobs_by_source)}
Keywords Searched: {len(keywords)}
Locations: {len(locations)}

"""
    
    # Add jobs grouped by source
    for source, source_jobs in jobs_by_source.items():
        text += f"\n{'=' * 60}\n"
        text += f"{source.upper()} ({len(source_jobs)} jobs)\n"
        text += f"{'=' * 60}\n\n"
        
        for i, job in enumerate(source_jobs, 1):
            title = job.get('title', 'N/A')
            company = job.get('company', 'N/A')
            location = job.get('location', 'N/A')
            url = job.get('url', 'N/A')
            salary = job.get('salary', '')
            scraped_at = job.get('scraped_at', 'N/A')
            
            text += f"{i}. {title}\n"
            text += f"   Company: {company}\n"
            text += f"   Location: {location}\n"
            
            if salary:
                text += f"   Salary: {salary}\n"
            
            text += f"   URL: {url}\n"
            text += f"   Scraped: {scraped_at}\n"
            text += f"\n"
    
    text += f"\n{'=' * 60}\n"
    text += "This is an automated job discovery report.\n"
    text += "Jobs are scraped from public job boards.\n"
    
    return text

def send_job_email(jobs: List[Dict], keywords: List[str], locations: List[str]) -> bool:
    """Send job listings via email"""
    try:
        # Get email configuration from environment
        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = int(os.getenv('SMTP_PORT', 465))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        smtp_encryption = os.getenv('SMTP_ENCRYPTION', 'ssl').lower()
        recipient = os.getenv('SMTP_RECIPIENT')
        
        if not all([smtp_host, smtp_username, smtp_password, recipient]):
            logger.error("Missing SMTP configuration in .env file")
            return False
        
        logger.info(f"Preparing to send email to {recipient}")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_username
        msg['To'] = recipient
        msg['Subject'] = f"Job Discovery Report - {len(jobs)} Jobs Found ({datetime.now().strftime('%Y-%m-%d')})"
        
        # Create plain text content
        text_content = create_text_email(jobs, keywords, locations)
        
        # Attach text content
        text_part = MIMEText(text_content, 'plain')
        msg.attach(text_part)
        
        # Send email
        logger.info(f"Connecting to SMTP server: {smtp_host}:{smtp_port}")
        
        if smtp_encryption == 'ssl':
            # Use SSL
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
        else:
            # Use TLS
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
            server.starttls()
        
        logger.info("Logging in to SMTP server...")
        server.login(smtp_username, smtp_password)
        
        logger.info("Sending email...")
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Email successfully sent to {recipient}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
