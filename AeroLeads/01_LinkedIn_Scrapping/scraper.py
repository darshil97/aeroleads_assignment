"""
LinkedIn Profile Scraper - Selenium Version
WARNING: This script is for educational purposes only.
Using automated scraping violates LinkedIn's Terms of Service and may result in account suspension.
"""
import random
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from config import Config


class LinkedInScraper:
    """LinkedIn profile scraper using Selenium with visible browser"""
    
    def __init__(self, visible: bool = True):
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.is_logged_in = False
        self.visible = visible
        
    def initialize(self):
        """Initialize Selenium WebDriver with Chrome"""
        chrome_options = Options()
        
        if not self.visible:
            chrome_options.add_argument('--headless')
        
        # Anti-detection measures
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set realistic window size
        chrome_options.add_argument('--window-size=1920,1080')
        
        # User agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize driver with automatic ChromeDriver management
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set implicit wait
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 20)
        
        # Execute CDP commands to prevent detection
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def random_delay(self, min_delay=None, max_delay=None):
        """Add random delay to mimic human behavior"""
        min_delay = min_delay or Config.MIN_DELAY
        max_delay = max_delay or Config.MAX_DELAY
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def human_like_typing(self, element, text: str):
        """Type text in a human-like manner"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
            
    def login(self, email: str, password: str) -> tuple[bool, str]:
        """
        Login to LinkedIn
        Returns: (success: bool, message: str)
        """
        try:
            self.driver.get(Config.LINKEDIN_LOGIN_URL)
            self.random_delay(2, 3)
            
            # Find and fill email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            self.human_like_typing(email_field, email)
            self.random_delay(0.5, 1.0)
            
            # Find and fill password
            password_field = self.driver.find_element(By.ID, "password")
            self.human_like_typing(password_field, password)
            self.random_delay(0.5, 1.0)
            
            # Click sign in button
            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            sign_in_button.click()
            
            # Wait for navigation
            self.random_delay(4, 6)
            
            # Check if login was successful
            current_url = self.driver.current_url
            
            if '/feed' in current_url or '/mynetwork' in current_url or 'linkedin.com/in/' in current_url:
                self.is_logged_in = True
                return True, "Successfully logged in to LinkedIn"
            elif '/checkpoint/challenge' in current_url:
                return False, "Login blocked - CAPTCHA or security challenge detected. Please solve it manually in the browser."
            else:
                # Check for error message
                try:
                    error_element = self.driver.find_element(By.CSS_SELECTOR, '.form__label--error')
                    error_text = error_element.text
                    return False, f"Login failed: {error_text}"
                except:
                    pass
                    
                # If no error and not on feed, might still be on login page
                if 'login' in current_url:
                    return False, "Login failed - Please check your credentials or solve any challenges in the browser"
                    
                # Assume success if we're somewhere else on LinkedIn
                self.is_logged_in = True
                return True, "Login appears successful"
                
        except Exception as e:
            return False, f"Login error: {str(e)}"
            
    def search_profiles(self, location: str = "", industry: str = "", max_profiles: int = 20) -> List[str]:
        """
        Search for LinkedIn profiles and return profile URLs
        Returns: List of profile URLs
        """
        if not self.is_logged_in:
            return []
            
        profile_urls = []
        
        try:
            # Navigate to people search
            search_url = Config.LINKEDIN_SEARCH_URL
            self.driver.get(search_url)
            self.random_delay(3, 5)
            
            # Scroll to load more profiles
            scroll_count = min(3, (max_profiles // 10) + 1)
            for i in range(scroll_count):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(2, 3)
                print(f"Scrolled {i+1}/{scroll_count} times")
            
            # Wait for search results to load
            self.random_delay(2, 3)
            
            # Method 1: Try finding profile links using Selenium (most reliable)
            try:
                # Find all links that contain '/in/' in href
                link_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")
                print(f"Found {len(link_elements)} potential profile links using Selenium")
                
                for idx, link_elem in enumerate(link_elements):
                    try:
                        href = link_elem.get_attribute('href')
                        
                        if href and '/in/' in href:
                            # Clean the URL FIRST (remove query params and fragments)
                            profile_url = href.split('?')[0].split('#')[0]
                            
                            # Check if cleaned URL contains miniProfile in the PATH (not query params)
                            # Also check it's a valid /in/ URL
                            if 'miniProfile' not in profile_url and '/in/' in profile_url:
                                # Make sure it's a unique profile URL
                                if profile_url not in profile_urls:
                                    profile_urls.append(profile_url)
                                    print(f"✓ Added profile {len(profile_urls)}: {profile_url}")
                                    
                                    if len(profile_urls) >= max_profiles:
                                        break
                    except Exception as e:
                        print(f"Error processing link {idx+1}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Method 1 failed: {e}")
            
            # Method 2: Try finding by specific search result container class
            if len(profile_urls) < max_profiles:
                try:
                    # LinkedIn often uses these classes for search results
                    search_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                        'li.reusable-search__result-container, div.search-result, div.entity-result')
                    print(f"Found {len(search_containers)} search result containers")
                    
                    for container in search_containers:
                        try:
                            # Try to find profile link within container
                            link = container.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
                            href = link.get_attribute('href')
                            if href:
                                profile_url = href.split('?')[0]
                                if profile_url not in profile_urls and '/in/' in profile_url:
                                    profile_urls.append(profile_url)
                                    print(f"Added profile from container: {profile_url}")
                                    
                                if len(profile_urls) >= max_profiles:
                                    break
                        except:
                            continue
                except Exception as e:
                    print(f"Method 2 failed: {e}")
            
            # Method 3: Fallback to BeautifulSoup with updated patterns
            if len(profile_urls) < max_profiles:
                try:
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    links = soup.find_all('a', href=True)
                    print(f"BeautifulSoup found {len(links)} total links")
                    
                    for link in links:
                        href = link.get('href', '')
                        if '/in/' in href and 'miniProfileUrn' not in href and 'miniProfile' not in href:
                            # Clean up the URL
                            if href.startswith('/'):
                                profile_url = f"https://www.linkedin.com{href}"
                            else:
                                profile_url = href
                            
                            profile_url = profile_url.split('?')[0]
                            
                            if profile_url not in profile_urls and profile_url.startswith('https://www.linkedin.com/in/'):
                                profile_urls.append(profile_url)
                                
                            if len(profile_urls) >= max_profiles:
                                break
                except Exception as e:
                    print(f"Method 3 failed: {e}")
            
            print(f"Total unique profiles found: {len(profile_urls)}")
            return profile_urls[:max_profiles]
            
        except Exception as e:
            print(f"Error searching profiles: {str(e)}")
            return profile_urls
            
    def scrape_profile(self, profile_url: str) -> Optional[Dict]:
        """
        Scrape data from a single LinkedIn profile
        Returns: Dictionary with profile data (Name, Headline, Location, Current Company, Current Position)
        """
        try:
            self.driver.get(profile_url)
            self.random_delay(2, 4)
            
            # Scroll to load content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
            self.random_delay(1, 2)
            
            profile_data = {
                'name': '',
                'headline': '',
                'location': '',
                'current_company': '',
                'current_position': ''
            }
            
            # Extract name - try multiple selectors
            try:
                # Method 1: Primary selector
                name_elem = self.driver.find_element(By.CSS_SELECTOR, 'h1.text-heading-xlarge')
                profile_data['name'] = name_elem.text.strip()
            except:
                try:
                    # Method 2: Alternative class
                    name_elem = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'inline')]")
                    profile_data['name'] = name_elem.text.strip()
                except:
                    try:
                        # Method 3: Find any h1 in profile section
                        name_elem = self.driver.find_element(By.XPATH, "//main//h1")
                        profile_data['name'] = name_elem.text.strip()
                    except:
                        print(f"Could not extract name from {profile_url}")
            
            # Extract headline - try multiple methods
            try:
                # Method 1: div with text-body-medium
                headline_elem = self.driver.find_element(By.CSS_SELECTOR, 'div.text-body-medium.break-words')
                profile_data['headline'] = headline_elem.text.strip()
            except:
                try:
                    # Method 2: Look for div under profile section
                    headline_elem = self.driver.find_element(By.XPATH, "//main//div[contains(@class, 'text-body-medium')]")
                    profile_data['headline'] = headline_elem.text.strip()
                except:
                    print(f"Could not extract headline from {profile_url}")
            
            # Extract location
            try:
                # Method 1: Span with location info
                location_elem = self.driver.find_element(By.CSS_SELECTOR, 'span.text-body-small.inline.t-black--light.break-words')
                profile_data['location'] = location_elem.text.strip()
            except:
                try:
                    # Method 2: Look for location in profile section
                    location_elem = self.driver.find_element(By.XPATH, "//main//span[contains(@class, 'text-body-small')]")
                    profile_data['location'] = location_elem.text.strip()
                except:
                    print(f"Could not extract location from {profile_url}")
            
            # Extract current position and company from headline
            # LinkedIn often formats headline as "Position at Company"
            headline = profile_data['headline']
            if headline:
                if ' at ' in headline or ' @ ' in headline:
                    # Split by @ or at
                    parts = headline.replace(' @ ', ' at ').split(' at ')
                    if len(parts) >= 2:
                        profile_data['current_position'] = parts[0].strip()
                        profile_data['current_company'] = parts[1].strip()
                else:
                    # If no clear separator, try to get from experience section
                    try:
                        # Look for experience section
                        exp_section = self.driver.find_element(By.ID, 'experience')
                        # Get first position
                        first_position = exp_section.find_element(By.CSS_SELECTOR, 'li.artdeco-list__item')
                        
                        # Try to get position title
                        try:
                            title_elem = first_position.find_element(By.CSS_SELECTOR, 'div[class*="display-flex"] span[aria-hidden="true"]')
                            profile_data['current_position'] = title_elem.text.strip()
                        except:
                            pass
                        
                        # Try to get company name
                        try:
                            company_elem = first_position.find_element(By.CSS_SELECTOR, 'span.t-14.t-normal span[aria-hidden="true"]')
                            profile_data['current_company'] = company_elem.text.strip()
                        except:
                            pass
                    except:
                        pass
            
            print(f"Scraped: {profile_data['name']} | {profile_data['headline'][:50] if profile_data['headline'] else 'No headline'}")
            return profile_data
            
        except Exception as e:
            print(f"Error scraping profile {profile_url}: {str(e)}")
            return None
            
    def scrape_profiles(self, profile_urls: List[str], progress_callback=None) -> List[Dict]:
        """
        Scrape multiple profiles with progress tracking
        """
        profiles_data = []
        total = len(profile_urls)
        
        for idx, url in enumerate(profile_urls, 1):
            if progress_callback:
                progress_callback(idx, total, f"Scraping profile {idx}/{total}")
            
            profile_data = self.scrape_profile(url)
            if profile_data:
                profiles_data.append(profile_data)
            
            # Add delay between profiles to avoid detection
            if idx < total:
                self.random_delay()
        
        return profiles_data
    
    def save_to_csv(self, profiles_data: List[Dict], filename: str = None):
        """Save scraped profiles to CSV file"""
        if not filename:
            filename = Config.get_output_path()
        
        df = pd.DataFrame(profiles_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        return filename
    
    def close(self):
        """Close browser"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            print(f"Error closing browser: {e}")


def run_scraper(email: str, password: str, location: str = "", 
                industry: str = "", max_profiles: int = 20, 
                progress_callback=None, visible: bool = True) -> tuple[bool, str, List[Dict]]:
    """
    Main function to run the scraper
    Returns: (success: bool, message: str, profiles_data: List[Dict])
    """
    scraper = LinkedInScraper(visible=visible)
    profiles_data = []
    
    try:
        # Initialize browser
        if progress_callback:
            progress_callback(0, max_profiles, "Initializing browser...")
        scraper.initialize()
        
        # Login
        if progress_callback:
            progress_callback(0, max_profiles, "Logging in to LinkedIn...")
        success, message = scraper.login(email, password)
        
        if not success:
            # Keep browser open if login failed so user can see/solve CAPTCHA
            if 'CAPTCHA' in message or 'challenge' in message:
                if progress_callback:
                    progress_callback(0, max_profiles, "Waiting for manual CAPTCHA solve...")
                # Wait for user to solve CAPTCHA and press Enter in terminal
                input("\n⚠️  Please solve the CAPTCHA in the browser window, then press Enter here to continue...")
                
                # Check if login succeeded after CAPTCHA solve
                current_url = scraper.driver.current_url
                if '/feed' in current_url or '/mynetwork' in current_url:
                    scraper.is_logged_in = True
                    success = True
                    message = "Login successful after CAPTCHA solve"
                else:
                    scraper.close()
                    return False, "Login still failed after CAPTCHA attempt", []
            else:
                scraper.close()
                return False, message, []
        
        # Search for profiles
        if progress_callback:
            progress_callback(0, max_profiles, "Searching for profiles...")
        profile_urls = scraper.search_profiles(location, industry, max_profiles)
        
        if not profile_urls:
            scraper.close()
            return False, "No profiles found with the given filters", []
        
        # Scrape profiles
        profiles_data = scraper.scrape_profiles(profile_urls, progress_callback)
        
        if not profiles_data:
            scraper.close()
            return False, "Failed to scrape any profile data", []
        
        # Save to CSV
        if progress_callback:
            progress_callback(len(profiles_data), max_profiles, "Saving data to CSV...")
        filename = scraper.save_to_csv(profiles_data)
        
        scraper.close()
        return True, f"Successfully scraped {len(profiles_data)} profiles. Data saved to {filename}", profiles_data
        
    except Exception as e:
        scraper.close()
        return False, f"Error during scraping: {str(e)}", profiles_data
