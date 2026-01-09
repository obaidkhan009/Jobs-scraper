"""
Dice.com Jobs scraper using Selenium.
Scrapes job listings from Dice tech jobs search.
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


class DiceScraper(BaseScraper):
    """Scraper for Dice.com tech jobs search results."""
    
    def __init__(self, headless: bool = False):
        """
        Initialize the Dice scraper.
        
        Args:
            headless: If True, run Chrome in headless mode
        """
        super().__init__("Dice")
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
        posted_within_hours: int = 48,
        page: int = 1
    ) -> str:
        """
        Build Dice search URL.
        
        Dice URL parameters:
        - q: search query
        - location: location
        - filters.postedDate: ONE, THREE, SEVEN (days)
        - filters.isRemote: true
        - page: page number
        """
        base_url = "https://www.dice.com/jobs"
        
        encoded_query = quote_plus(query)
        
        # Build query parameters
        params = [
            f"q={encoded_query}",
            "countryCode=US",
            "radius=30",
            "radiusUnit=mi",
            "language=en",
        ]
        
        # Remote filter
        if remote_only:
            params.append("filters.isRemote=true")
        
        # Location
        if location:
            params.append(f"location={quote_plus(location)}")
        
        # Time filter (Dice uses ONE, THREE, SEVEN for days)
        if posted_within_hours <= 24:
            params.append("filters.postedDate=ONE")
        elif posted_within_hours <= 72:
            params.append("filters.postedDate=THREE")
        elif posted_within_hours <= 168:
            params.append("filters.postedDate=SEVEN")
        
        # Pagination
        if page > 1:
            params.append(f"page={page}")
        
        return f"{base_url}?{'&'.join(params)}"
    
    def search(
        self,
        query: str,
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> List[Job]:
        """Search Dice for matching positions."""
        all_jobs = []
        
        print(f"[Dice] Searching: {query}")
        
        # Search first 2 pages
        for page in range(1, 3):
            url = self._build_search_url(query, location, remote_only, posted_within_hours, page)
            
            try:
                self.driver.get(url)
                time.sleep(3)
                
                # Collect jobs from this page
                jobs = self._collect_jobs()
                
                if len(jobs) == 0:
                    break
                    
                all_jobs.extend(jobs)
                
            except Exception as e:
                print(f"[Dice] Error on page {page}: {e}")
                break
        
        print(f"[Dice] Found {len(all_jobs)} jobs for '{query}'")
        return all_jobs
    
    def _collect_jobs(self) -> List[Job]:
        """Collect jobs from the Dice search results page."""
        jobs = []
        
        # Use JavaScript to extract job data
        job_data = self.driver.execute_script("""
            const jobs = [];
            
            // Dice job cards - try multiple selectors
            const jobCards = document.querySelectorAll(
                'dhi-search-card, ' +
                '[data-cy="search-card"], ' +
                '.dhi-job-search-card'
            );
            
            // Fallback to generic card selection
            const allCards = jobCards.length > 0 ? jobCards : document.querySelectorAll('[data-testid*="job"], .search-card');
            
            allCards.forEach((card, index) => {
                try {
                    // Job title - Dice uses specific selectors
                    const titleEl = card.querySelector(
                        'a[data-cy="card-title-link"], ' +
                        '.card-title-link, ' +
                        'h5 a, ' +
                        'a.card-title-link'
                    );
                    
                    // Company name
                    const companyEl = card.querySelector(
                        '[data-cy="search-result-company-name"], ' +
                        '.card-company, ' +
                        'a[data-cy*="company"]'
                    );
                    
                    // Location
                    const locationEl = card.querySelector(
                        '[data-cy="search-result-location"], ' +
                        '.card-location, ' +
                        'span[data-cy*="location"]'
                    );
                    
                    // Posted date - improved extraction
                    let datePosted = '';
                    const dateEl = card.querySelector(
                        '[data-cy="card-posted-date"], ' +
                        '.posted-date, ' +
                        'span[data-cy*="posted"]'
                    );
                    
                    if (dateEl) {
                        datePosted = dateEl.innerText.trim();
                    } else {
                        // Fallback: search for "ago" pattern in the card text
                        const cardText = card.innerText || '';
                        const agoMatch = cardText.match(/(\\d+\\s*(hours?|days?|weeks?|months?)\\s*ago|today|yesterday)/i);
                        if (agoMatch) {
                            datePosted = agoMatch[0];
                        }
                    }
                    
                    // Job link
                    const linkEl = titleEl || card.querySelector('a[href*="/job-detail/"]');
                    
                    const title = titleEl ? titleEl.innerText.trim() : '';
                    const company = companyEl ? companyEl.innerText.trim() : '';
                    const location = locationEl ? locationEl.innerText.trim() : '';
                    let url = linkEl ? linkEl.href : '';
                    
                    // Make sure URL is absolute
                    if (url && !url.startsWith('http')) {
                        url = 'https://www.dice.com' + url;
                    }
                    
                    if (title) {
                        jobs.push({
                            title: title,
                            company: company,
                            location: location,
                            url: url,
                            datePosted: datePosted || 'Recently',
                            index: index
                        });
                    }
                } catch(e) {
                    console.error('Error parsing Dice job card:', e);
                }
            });
            
            return jobs;
        """)
        
        if not job_data:
            print("[Dice] No job cards found, trying alternative extraction...")
            job_data = self._extract_jobs_fallback()
        
        # Process each job
        for jd in job_data[:20]:  # Limit per page
            try:
                job = Job(
                    title=jd.get('title', '').strip(),
                    company=jd.get('company', '').strip(),
                    location=jd.get('location', '').strip(),
                    salary='',  # Dice doesn't always show salary in search
                    url=jd.get('url', ''),
                    platform=self.platform_name,
                    date_posted=jd.get('datePosted', ''),
                    description=''
                )
                
                if job.title:
                    jobs.append(job)
                    
            except Exception as e:
                print(f"[Dice] Error processing job: {e}")
                continue
        
        return jobs
    
    def _extract_jobs_fallback(self) -> list:
        """Fallback extraction method."""
        try:
            return self.driver.execute_script("""
                const jobs = [];
                
                // Try to find any links that look like job postings
                document.querySelectorAll('a').forEach((link, index) => {
                    const href = link.href || '';
                    const text = link.innerText.trim();
                    
                    if (href.includes('/job-detail/') && text.length > 5 && text.length < 100) {
                        // Try to find company and location from siblings/parent
                        const parent = link.closest('div, article, li');
                        const parentText = parent ? parent.innerText : '';
                        const lines = parentText.split('\\n').filter(l => l.trim());
                        
                        jobs.push({
                            title: text,
                            company: lines[1] || '',
                            location: lines[2] || '',
                            url: href,
                            datePosted: '',
                            index: index
                        });
                    }
                });
                
                // Deduplicate by title
                const seen = new Set();
                return jobs.filter(job => {
                    if (seen.has(job.title)) return false;
                    seen.add(job.title);
                    return true;
                }).slice(0, 25);
            """)
        except:
            return []
    
    def get_job_details(self, job: Job) -> Job:
        """Fetch additional details for a job."""
        return job
    
    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
