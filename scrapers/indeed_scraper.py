"""
Indeed Jobs scraper using Selenium.
Scrapes job listings from Indeed search without requiring login.
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


class IndeedScraper(BaseScraper):
    """Scraper for Indeed Jobs search results."""
    
    def __init__(self, headless: bool = False):
        """
        Initialize the Indeed scraper.
        
        Args:
            headless: If True, run Chrome in headless mode
        """
        super().__init__("Indeed")
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
        page: int = 0
    ) -> str:
        """
        Build Indeed search URL.
        
        Indeed URL parameters:
        - q: search query
        - l: location
        - sc: filters (0kf:attr(DSQF7)  = remote)
        - fromage: days since posted (1, 3, 7, 14)
        - start: pagination (0, 10, 20, ...)
        - salary: minimum salary filter
        """
        base_url = "https://www.indeed.com/jobs"
        
        # Add remote to query for better results
        search_query = query
        if remote_only:
            search_query += " remote"
        
        encoded_query = quote_plus(search_query)
        encoded_location = quote_plus(location)
        
        # Build query parameters
        params = [
            f"q={encoded_query}",
            f"l={encoded_location}",
        ]
        
        # Remote filter
        if remote_only:
            params.append("sc=0kf%3Aattr%28DSQF7%29%3B")  # Remote filter
        
        # Time filter
        if posted_within_hours <= 24:
            params.append("fromage=1")  # Last 24 hours
        elif posted_within_hours <= 72:
            params.append("fromage=3")  # Last 3 days
        elif posted_within_hours <= 168:
            params.append("fromage=7")  # Last week
        
        # Pagination
        if page > 0:
            params.append(f"start={page * 10}")
        
        return f"{base_url}?{'&'.join(params)}"
    
    def search(
        self,
        query: str,
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> List[Job]:
        """Search Indeed for matching positions."""
        all_jobs = []
        
        print(f"[Indeed] Searching: {query}")
        
        # Search first 2 pages to get more results
        for page in range(2):
            url = self._build_search_url(query, location, remote_only, posted_within_hours, page)
            
            try:
                self.driver.get(url)
                time.sleep(3)  # Wait for page to load
                
                # Handle potential CAPTCHA or popup
                self._handle_popups()
                
                # Collect jobs from this page
                jobs = self._collect_jobs()
                all_jobs.extend(jobs)
                
                if len(jobs) == 0:
                    break  # No more results
                    
            except Exception as e:
                print(f"[Indeed] Error on page {page}: {e}")
                break
        
        print(f"[Indeed] Found {len(all_jobs)} jobs for '{query}'")
        return all_jobs
    
    def _handle_popups(self):
        """Handle any popups or modals that might appear."""
        try:
            # Close email popup if present
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                'button[aria-label="close"], .icl-CloseButton, [data-testid="close-button"]')
            for btn in close_buttons:
                try:
                    btn.click()
                    time.sleep(0.5)
                except:
                    pass
        except:
            pass
    
    def _collect_jobs(self) -> List[Job]:
        """Collect jobs from the Indeed search results page."""
        jobs = []
        
        # Use JavaScript to extract job data
        job_data = self.driver.execute_script("""
            const jobs = [];
            
            // Indeed job cards - multiple possible selectors
            const jobCards = document.querySelectorAll(
                '.job_seen_beacon, ' +
                '.jobsearch-ResultsList > li, ' +
                '[data-testid="job-card"], ' +
                '.resultContent'
            );
            
            jobCards.forEach((card, index) => {
                try {
                    // Job title
                    const titleEl = card.querySelector(
                        'h2.jobTitle a, ' +
                        '.jobTitle span, ' +
                        'a[data-jk], ' +
                        '.jobTitle'
                    );
                    
                    // Company name  
                    const companyEl = card.querySelector(
                        '[data-testid="company-name"], ' +
                        '.companyName, ' +
                        '.company_location .companyName'
                    );
                    
                    // Location
                    const locationEl = card.querySelector(
                        '[data-testid="text-location"], ' +
                        '.companyLocation, ' +
                        '.company_location .companyLocation'
                    );
                    
                    // Salary
                    const salaryEl = card.querySelector(
                        '.salary-snippet-container, ' +
                        '.salaryText, ' +
                        '[data-testid="attribute_snippet_testid"]'
                    );
                    
                    // Job link
                    const linkEl = card.querySelector('a[data-jk], h2.jobTitle a, a[id^="job_"]');
                    
                    // Date posted
                    const dateEl = card.querySelector('.date, [data-testid="myJobsStateDate"]');
                    
                    const title = titleEl ? titleEl.innerText.trim() : '';
                    const company = companyEl ? companyEl.innerText.trim() : '';
                    const location = locationEl ? locationEl.innerText.trim() : '';
                    const salary = salaryEl ? salaryEl.innerText.trim() : '';
                    const datePosted = dateEl ? dateEl.innerText.trim() : '';
                    
                    // Get job URL
                    let url = '';
                    if (linkEl) {
                        const jk = linkEl.getAttribute('data-jk') || linkEl.getAttribute('href');
                        if (jk && jk.startsWith('/')) {
                            url = 'https://www.indeed.com' + jk;
                        } else if (jk && jk.includes('indeed.com')) {
                            url = jk;
                        } else if (jk) {
                            url = 'https://www.indeed.com/viewjob?jk=' + jk;
                        }
                    }
                    
                    if (title && company) {
                        jobs.push({
                            title: title,
                            company: company,
                            location: location,
                            salary: salary,
                            url: url,
                            datePosted: datePosted,
                            index: index
                        });
                    }
                } catch(e) {
                    console.error('Error parsing Indeed job card:', e);
                }
            });
            
            return jobs;
        """)
        
        if not job_data:
            print("[Indeed] No job cards found, trying alternative extraction...")
            job_data = self._extract_jobs_fallback()
        
        # Process each job
        for jd in job_data[:15]:  # Limit per page
            try:
                # Filter USD salaries only
                salary = jd.get('salary', '')
                if salary and ('$' not in salary):
                    continue  # Skip non-USD
                
                job = Job(
                    title=jd.get('title', '').strip(),
                    company=jd.get('company', '').strip(),
                    location=jd.get('location', '').strip(),
                    salary=salary,
                    url=jd.get('url', ''),
                    platform=self.platform_name,
                    date_posted=jd.get('datePosted', ''),
                    description=''
                )
                
                if job.title and job.company:
                    jobs.append(job)
                    
            except Exception as e:
                print(f"[Indeed] Error processing job: {e}")
                continue
        
        return jobs
    
    def _extract_jobs_fallback(self) -> list:
        """Fallback extraction method."""
        try:
            return self.driver.execute_script("""
                const jobs = [];
                
                // Try to find any elements that look like job listings
                document.querySelectorAll('li, article').forEach((el, index) => {
                    const text = el.innerText || '';
                    const links = el.querySelectorAll('a');
                    
                    // Check if it looks like a job listing
                    if (text.length > 50 && text.length < 1000) {
                        const lines = text.split('\\n').filter(l => l.trim());
                        
                        if (lines.length >= 2) {
                            let jobUrl = '';
                            for (const link of links) {
                                if (link.href && (link.href.includes('/viewjob') || link.href.includes('jk='))) {
                                    jobUrl = link.href;
                                    break;
                                }
                            }
                            
                            if (jobUrl || lines[0].length < 100) {
                                jobs.push({
                                    title: lines[0],
                                    company: lines[1],
                                    location: lines[2] || '',
                                    salary: '',
                                    url: jobUrl,
                                    datePosted: '',
                                    index: index
                                });
                            }
                        }
                    }
                });
                
                return jobs.slice(0, 20);
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
