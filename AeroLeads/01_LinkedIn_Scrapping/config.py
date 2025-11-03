"""
Configuration module for LinkedIn Scraper (Local MacBook Version)
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for LinkedIn scraper settings"""
    
    # LinkedIn Credentials (from .env file)
    LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL', '')
    LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', '')
    
    # Scraping Settings
    MIN_DELAY = 3  # Minimum delay between actions (seconds)
    MAX_DELAY = 7  # Maximum delay between actions (seconds)
    DEFAULT_PROFILES_TO_SCRAPE = 20
    MAX_PROFILES_LIMIT = 20  # Maximum profiles per session
    
    # LinkedIn URLs
    LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
    LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
    LINKEDIN_SEARCH_URL = "https://www.linkedin.com/search/results/people/"
    
    # Data Storage (Local)
    DATA_DIR = "data"
    OUTPUT_CSV = "linkedin_profiles.csv"
    
    @classmethod
    def validate_credentials(cls):
        """Validate that credentials are set"""
        if not cls.LINKEDIN_EMAIL or not cls.LINKEDIN_PASSWORD:
            return False, "LinkedIn credentials not found. Please create a .env file with LINKEDIN_EMAIL and LINKEDIN_PASSWORD."
        return True, "Credentials validated"
    
    @classmethod
    def get_output_path(cls):
        """Get full path for output CSV file"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        return os.path.join(cls.DATA_DIR, cls.OUTPUT_CSV)
