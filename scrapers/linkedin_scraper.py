"""
LinkedIn Jobs scraper using Selenium.
Scrapes job listings from LinkedIn Jobs search without requiring login.
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


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn Jobs search results (no login required for search)."""
    
    def __init__(self, headless: bool = False):
        """
        Initialize the LinkedIn scraper.
        
        Args:
            headless: If True, run Chrome in headless mode
        """
        super().__init__("LinkedIn")
        self.headless = headless
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        """Initialize the Chrome WebDriver."""
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
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> str:
        """
        Build LinkedIn Jobs search URL.
        
        LinkedIn URL parameters:
        - keywords: search query
        - location: location filter
        - f_WT: work type (2 = remote)
        - f_TPR: time posted (r86400 = 24h, r604800 = week)
        - f_SB2: salary (6 = $120k+)
        """
        base_url = "https://www.linkedin.com/jobs/search"
        
        encoded_query = quote_plus(query)
        encoded_location = quote_plus(location)
        
        # Build query parameters
        params = [
            f"keywords={encoded_query}",
            f"location={encoded_location}",
        ]
        
        # Remote filter
        if remote_only:
            params.append("f_WT=2")  # 2 = Remote
        
        # Time filter
        if posted_within_hours <= 24:
            params.append("f_TPR=r86400")  # Past 24 hours
        elif posted_within_hours <= 168:
            params.append("f_TPR=r604800")  # Past week
        else:
            params.append("f_TPR=r2592000")  # Past month
        
        # Salary filter - $120k+ (salary bucket 6)
        params.append("f_SB2=6")
        
        return f"{base_url}?{'&'.join(params)}"
    
    def search(
        self,
        query: str,
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> List[Job]:
        """Search LinkedIn Jobs for matching positions."""
        jobs = []
        url = self._build_search_url(query, location, remote_only, posted_within_hours)
        
        print(f"[LinkedIn] Searching: {query}")
        
        try:
            self.driver.get(url)
            time.sleep(4)  # Wait for page to load
            
            # Scroll to load more jobs
            self._scroll_to_load_jobs()
            
            # Extract jobs
            jobs = self._collect_jobs()
            
            print(f"[LinkedIn] Found {len(jobs)} jobs for '{query}'")
            
        except Exception as e:
            print(f"[LinkedIn] Error searching: {e}")
            import traceback
            traceback.print_exc()
        
        return jobs
    
    def _scroll_to_load_jobs(self):
        """Scroll the page to load more job listings."""
        try:
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(1)
            # Scroll back up
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
        except:
            pass
    
    def _collect_jobs(self) -> List[Job]:
        """Collect jobs from the LinkedIn search results page."""
        jobs = []
        
        # Use JavaScript to extract job data
        job_data = self.driver.execute_script("""
            const jobs = [];
            
            // LinkedIn job cards - multiple possible selectors
            const jobCards = document.querySelectorAll(
                '.jobs-search__results-list li, ' +
                '.job-search-card, ' +
                '[data-occludable-job-id], ' +
                '.base-card'
            );
            
            jobCards.forEach((card, index) => {
                try {
                    // Job title
                    const titleEl = card.querySelector(
                        '.base-search-card__title, ' +
                        '.job-search-card__title, ' +
                        'h3.base-search-card__title, ' +
                        'a[data-tracking-control-name*="job"] span'
                    );
                    
                    // Company name
                    const companyEl = card.querySelector(
                        '.base-search-card__subtitle, ' +
                        '.job-search-card__company-name, ' +
                        'h4.base-search-card__subtitle, ' +
                        'a[data-tracking-control-name*="company"]'
                    );
                    
                    // Location
                    const locationEl = card.querySelector(
                        '.job-search-card__location, ' +
                        '.base-search-card__metadata span'
                    );
                    
                    // Job link
                    const linkEl = card.querySelector('a.base-card__full-link, a[data-tracking-control-name*="job"]');
                    
                    // Date posted
                    const dateEl = card.querySelector('time, .job-search-card__listdate');
                    
                    const title = titleEl ? titleEl.innerText.trim() : '';
                    const company = companyEl ? companyEl.innerText.trim() : '';
                    const location = locationEl ? locationEl.innerText.trim() : '';
                    const url = linkEl ? linkEl.href : '';
                    const datePosted = dateEl ? (dateEl.getAttribute('datetime') || dateEl.innerText.trim()) : '';
                    
                    if (title && company) {
                        jobs.push({
                            title: title,
                            company: company,
                            location: location,
                            url: url,
                            datePosted: datePosted,
                            index: index
                        });
                    }
                } catch(e) {
                    console.error('Error parsing LinkedIn job card:', e);
                }
            });
            
            return jobs;
        """)
        
        if not job_data:
            print("[LinkedIn] No job cards found, trying alternative extraction...")
            job_data = self._extract_jobs_fallback()
        
        print(f"[LinkedIn] Extracted {len(job_data)} job cards")
        
        # Process each job
        for jd in job_data[:40]:  # Get up to 40 jobs per search
            try:
                job = Job(
                    title=jd.get('title', '').strip(),
                    company=jd.get('company', '').strip(),
                    location=jd.get('location', '').strip(),
                    url=jd.get('url', ''),
                    platform=self.platform_name,
                    date_posted=jd.get('datePosted', ''),
                    salary='',  # LinkedIn doesn't always show salary in search
                    description=''  # Would need to click each job to get description
                )
                
                if job.title and job.company:
                    jobs.append(job)
                    
            except Exception as e:
                print(f"[LinkedIn] Error processing job: {e}")
                continue
        
        return jobs
    
    def _extract_jobs_fallback(self) -> list:
        """Fallback extraction method using alternative selectors."""
        try:
            return self.driver.execute_script("""
                const jobs = [];
                
                // Try to find any list items that look like job cards
                document.querySelectorAll('li').forEach((el, index) => {
                    const text = el.innerText || '';
                    const links = el.querySelectorAll('a');
                    
                    // Check if it looks like a job listing
                    if (text.length > 50 && text.length < 500 && links.length > 0) {
                        const lines = text.split('\\n').filter(l => l.trim());
                        
                        if (lines.length >= 2) {
                            // Find a job-like link
                            let jobUrl = '';
                            for (const link of links) {
                                if (link.href && link.href.includes('/jobs/')) {
                                    jobUrl = link.href;
                                    break;
                                }
                            }
                            
                            if (jobUrl) {
                                jobs.push({
                                    title: lines[0],
                                    company: lines[1],
                                    location: lines[2] || '',
                                    url: jobUrl,
                                    datePosted: '',
                                    index: index
                                });
                            }
                        }
                    }
                });
                
                return jobs.slice(0, 30);
            """)
        except:
            return []
    
    def get_job_details(self, job: Job) -> Job:
        """
        Fetch additional details for a job by visiting its URL.
        Note: This would require navigating to each job page.
        """
        # For now, return as is - description would require clicking each job
        return job
    
    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
