"""
ZipRecruiter Jobs scraper.

ZipRecruiter is one of the largest job boards with millions of listings.
Uses Selenium due to dynamic JavaScript rendering.
"""

import time
import re
from typing import List, Optional
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from .base_scraper import BaseScraper, Job


class ZipRecruiterScraper(BaseScraper):
    """Scraper for ZipRecruiter job listings."""
    
    BASE_URL = "https://www.ziprecruiter.com/jobs-search"
    
    def __init__(self, headless: bool = True):
        """Initialize the ZipRecruiter scraper."""
        super().__init__("ZipRecruiter")
        self.headless = headless
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """Initialize Chrome WebDriver."""
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        
        # Remove webdriver detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def _build_search_url(
        self,
        query: str,
        location: str = "Remote",
        remote_only: bool = True,
        days: int = 1
    ) -> str:
        """Build ZipRecruiter search URL."""
        encoded_query = quote_plus(query)
        
        if remote_only:
            location = "Remote"
        
        encoded_location = quote_plus(location)
        
        # days: 1 = last 24 hours, 3 = last 3 days, 7 = last week
        url = f"{self.BASE_URL}?search={encoded_query}&location={encoded_location}&days={days}"
        
        return url
    
    def search(
        self,
        query: str,
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> List[Job]:
        """Search ZipRecruiter for jobs."""
        jobs = []
        
        # Convert hours to days for ZipRecruiter
        if posted_within_hours <= 24:
            days = 1
        elif posted_within_hours <= 72:
            days = 3
        else:
            days = 7
        
        url = self._build_search_url(query, location, remote_only, days)
        
        print(f"[ZipRecruiter] Searching: {query}")
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Extract jobs using JavaScript
            jobs = self._extract_jobs()
            
            print(f"[ZipRecruiter] Found {len(jobs)} jobs for '{query}'")
            
        except Exception as e:
            print(f"[ZipRecruiter] Error: {e}")
        
        return jobs
    
    def _extract_jobs(self) -> List[Job]:
        """Extract job listings from the page."""
        jobs = []
        
        try:
            # Wait for job cards to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article.job_result, .job_content, .jobList"))
            )
        except TimeoutException:
            print("[ZipRecruiter] No job results found")
            return jobs
        
        # Use JavaScript to extract job data
        job_data = self.driver.execute_script("""
            const jobs = [];
            
            // Try multiple selectors for job cards
            const selectors = [
                'article.job_result',
                '.job_content',
                '[data-testid="job-card"]',
                '.jobList article'
            ];
            
            let cards = [];
            for (const sel of selectors) {
                cards = document.querySelectorAll(sel);
                if (cards.length > 0) break;
            }
            
            cards.forEach(card => {
                try {
                    // Title
                    const titleEl = card.querySelector('h2, .job_title, [data-testid="job-title"], .jobTitle');
                    const title = titleEl ? titleEl.innerText.trim() : '';
                    
                    // Company
                    const companyEl = card.querySelector('.company_name, .hiring_company, [data-testid="company-name"]');
                    const company = companyEl ? companyEl.innerText.trim() : '';
                    
                    // Location
                    const locationEl = card.querySelector('.location, .job_location, [data-testid="job-location"]');
                    const location = locationEl ? locationEl.innerText.trim() : '';
                    
                    // Salary
                    const salaryEl = card.querySelector('.salary, .compensation, [data-testid="salary"]');
                    const salary = salaryEl ? salaryEl.innerText.trim() : '';
                    
                    // Date posted
                    const dateEl = card.querySelector('.posted_date, .job_date, time');
                    const datePosted = dateEl ? dateEl.innerText.trim() : '';
                    
                    // URL
                    const linkEl = card.querySelector('a[href*="/job/"], a.job_link, h2 a');
                    const url = linkEl ? linkEl.href : '';
                    
                    // Description snippet
                    const descEl = card.querySelector('.job_snippet, .job_description, p');
                    const description = descEl ? descEl.innerText.trim() : '';
                    
                    if (title && company) {
                        jobs.push({
                            title: title,
                            company: company,
                            location: location,
                            salary: salary,
                            datePosted: datePosted,
                            url: url,
                            description: description
                        });
                    }
                } catch(e) {
                    console.error('Error parsing job card:', e);
                }
            });
            
            return jobs;
        """)
        
        # Convert to Job objects
        for jd in (job_data or []):
            try:
                job = Job(
                    title=jd.get('title', ''),
                    company=jd.get('company', ''),
                    location=jd.get('location', ''),
                    salary=jd.get('salary', ''),
                    description=jd.get('description', ''),
                    url=jd.get('url', ''),
                    platform=self.platform_name,
                    date_posted=jd.get('datePosted', ''),
                    job_type=''
                )
                jobs.append(job)
            except Exception as e:
                print(f"[ZipRecruiter] Error creating job: {e}")
                continue
        
        return jobs
    
    def get_job_details(self, job: Job) -> Job:
        """Get additional job details."""
        return job
    
    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
