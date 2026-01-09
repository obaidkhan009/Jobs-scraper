"""
Google Jobs scraper using Selenium with correct selectors identified via browser inspection.
"""

import time
import re
import json
from typing import List, Optional
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from .base_scraper import BaseScraper, Job


class GoogleJobsScraper(BaseScraper):
    """Scraper for Google Jobs search results."""
    
    # Updated selectors based on browser inspection (Jan 2026)
    SELECTORS = {
        'job_card': 'a.MQUd2b',           # Job card container link
        'job_title': '.tNxQIb, .PUpOsf',   # Job title
        'company': '.wHYlTd.MKCbgd.a3jPc', # Company name
        'location': '.wHYlTd.FqK3wc.MKCbgd, .FqK3wc', # Location
        'date_posted': '.SuWscb, [data-ved] span',  # Date posted
        'job_type': '.LimNGf',             # Full-time, Part-time, etc.
        'description': '.OLKT8d, .HBvzbc', # Job description
        'apply_link': 'a[aria-label^="Apply on"], .nNzjpf-cS4Vcb-PvZLI-Ueh9jd-LgbsSe-Jyewjb-tlSJBe',
        'salary': '.SuWscb',               # Salary info
    }
    
    def __init__(self, headless: bool = False):
        """
        Initialize the Google Jobs scraper.
        
        Args:
            headless: If True, run Chrome in headless mode
        """
        super().__init__("Google Jobs")
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
        remote_only: bool = True
    ) -> str:
        """Build Google Jobs search URL."""
        search_query = f"{query}"
        if remote_only:
            search_query += " remote"
        if location:
            search_query += f" {location}"
        
        encoded_query = quote_plus(search_query)
        return f"https://www.google.com/search?q={encoded_query}&ibp=htl;jobs"
    
    def search(
        self,
        query: str,
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> List[Job]:
        """Search Google Jobs for matching positions."""
        jobs = []
        url = self._build_search_url(query, location, remote_only)
        
        print(f"[GoogleJobs] Searching: {query}")
        
        try:
            self.driver.get(url)
            time.sleep(4)  # Wait for page to load
            
            # Apply date filter if needed
            self._apply_date_filter(posted_within_hours)
            time.sleep(2)
            
            # Collect jobs using JavaScript
            jobs = self._collect_jobs_js()
            
            print(f"[GoogleJobs] Found {len(jobs)} jobs for '{query}'")
            
        except Exception as e:
            print(f"[GoogleJobs] Error searching: {e}")
            import traceback
            traceback.print_exc()
        
        return jobs
    
    def _apply_date_filter(self, posted_within_hours: int):
        """Apply date posted filter."""
        try:
            # Click on "Date posted" dropdown
            date_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                "button[aria-label*='Date'], span.pXXrrc, .x3snld")
            
            for btn in date_buttons:
                btn_text = btn.text.lower()
                if 'date' in btn_text or 'posted' in btn_text:
                    btn.click()
                    time.sleep(1)
                    break
            
            # Select appropriate date range
            if posted_within_hours <= 24:
                target_texts = ["24 hours", "past 24 hours", "today"]
            elif posted_within_hours <= 72:
                target_texts = ["3 days", "past 3 days"]
            else:
                target_texts = ["week", "past week"]
            
            # Find and click the option
            options = self.driver.find_elements(By.CSS_SELECTOR, 
                "li[role='menuitem'], div[role='option'], g-menu-item")
            
            for opt in options:
                opt_text = opt.text.lower()
                for target in target_texts:
                    if target in opt_text:
                        opt.click()
                        return
                        
        except Exception as e:
            print(f"[GoogleJobs] Date filter not applied: {e}")
    
    def _collect_jobs_js(self) -> List[Job]:
        """Collect jobs using JavaScript for reliability."""
        jobs = []
        
        # First, scroll to load more jobs
        self._scroll_to_load_jobs()
        
        # Use JavaScript to extract job data
        job_data = self.driver.execute_script("""
            const jobs = [];
            
            // Find all job card links using the MQUd2b selector
            const jobCards = document.querySelectorAll('a.MQUd2b');
            
            jobCards.forEach((card, index) => {
                try {
                    const titleEl = card.querySelector('.tNxQIb, .PUpOsf');
                    const companyEl = card.querySelector('.wHYlTd.MKCbgd.a3jPc, .OSrXXb .wHYlTd');
                    const locationEl = card.querySelector('.wHYlTd.FqK3wc.MKCbgd, .FqK3wc');
                    
                    // Get all text content as fallback
                    const allText = card.innerText.split('\\n').filter(l => l.trim());
                    
                    const title = titleEl ? titleEl.innerText.trim() : (allText[0] || '');
                    const company = companyEl ? companyEl.innerText.trim() : (allText[1] || '');
                    
                    // Location might include platform like "via LinkedIn"
                    let location = locationEl ? locationEl.innerText.trim() : (allText[2] || '');
                    
                    // Find date and job type from remaining elements
                    let datePosted = '';
                    let jobType = '';
                    
                    const spans = card.querySelectorAll('span');
                    spans.forEach(span => {
                        const text = span.innerText.trim().toLowerCase();
                        
                        // Match various date patterns
                        if (!datePosted) {
                            // "X hours ago", "X days ago", "X weeks ago"
                            if (text.match(/^\d+\s*(hour|day|week|month)s?\s*ago$/i)) {
                                datePosted = span.innerText.trim();
                            }
                            // "today", "yesterday"
                            else if (text === 'today' || text === 'yesterday') {
                                datePosted = span.innerText.trim();
                            }
                            // "just now", "just posted"
                            else if (text.includes('just now') || text.includes('just posted')) {
                                datePosted = 'Just now';
                            }
                            // Check for "posted X ago" format
                            else if (text.includes('posted') && text.includes('ago')) {
                                const match = text.match(/(\d+\s*(hour|day|week|month)s?\s*ago)/i);
                                if (match) datePosted = match[1];
                            }
                        }
                        
                        if (text.includes('full-time') || text.includes('part-time') || 
                            text.includes('contract') || text.includes('intern')) {
                            jobType = span.innerText.trim();
                        }
                    });
                    
                    // Fallback: check parent container for date info
                    if (!datePosted) {
                        const cardText = card.innerText.toLowerCase();
                        const dateMatch = cardText.match(/(\d+)\s*(hour|day|week|month)s?\s*ago/i);
                        if (dateMatch) {
                            datePosted = dateMatch[0];
                        }
                    }
                    
                    if (title) {
                        jobs.push({
                            title: title,
                            company: company,
                            location: location,
                            datePosted: datePosted,
                            jobType: jobType,
                            index: index
                        });
                    }
                } catch(e) {
                    console.error('Error parsing job card:', e);
                }
            });
            
            return jobs;
        """)
        
        if not job_data:
            print("[GoogleJobs] No job cards found with primary selector, trying fallback...")
            job_data = self._extract_jobs_fallback()
        
        print(f"[GoogleJobs] Extracted {len(job_data)} job cards")
        
        # Process each job to get details
        for i, jd in enumerate(job_data[:50]):  # Get up to 50 jobs per search
            try:
                job = self._process_job(jd, i)
                if job:
                    jobs.append(job)
            except Exception as e:
                print(f"[GoogleJobs] Error processing job {i}: {e}")
                continue
        
        return jobs
    
    def _scroll_to_load_jobs(self):
        """Scroll the job panel to load more results."""
        try:
            for _ in range(3):
                self.driver.execute_script("""
                    const panel = document.querySelector('[role="list"]');
                    if (panel) {
                        panel.scrollBy(0, 500);
                    } else {
                        const cards = document.querySelectorAll('a.MQUd2b');
                        if (cards.length > 0) {
                            cards[cards.length - 1].scrollIntoView(false);
                        }
                    }
                """)
                time.sleep(0.8)
        except:
            pass
    
    def _extract_jobs_fallback(self) -> list:
        """Fallback extraction method."""
        try:
            return self.driver.execute_script("""
                const jobs = [];
                
                // Try alternative selectors
                const cards = document.querySelectorAll('[data-ved] li, .K7076c');
                
                cards.forEach((card, index) => {
                    const text = card.innerText || '';
                    const lines = text.split('\\n').filter(l => l.trim());
                    
                    if (lines.length >= 2 && 
                        (text.toLowerCase().includes('developer') || 
                         text.toLowerCase().includes('engineer') ||
                         text.toLowerCase().includes('remote'))) {
                        jobs.push({
                            title: lines[0],
                            company: lines[1],
                            location: lines[2] || '',
                            datePosted: '',
                            jobType: '',
                            index: index
                        });
                    }
                });
                
                return jobs;
            """)
        except:
            return []
    
    def _process_job(self, job_data: dict, index: int) -> Optional[Job]:
        """Process a single job, clicking to get details."""
        title = job_data.get('title', '').strip()
        company = job_data.get('company', '').strip()
        
        if not title:
            return None
        
        # Click on the job card to load details
        try:
            self.driver.execute_script(f"""
                const cards = document.querySelectorAll('a.MQUd2b');
                if (cards[{job_data.get('index', index)}]) {{
                    cards[{job_data.get('index', index)}].click();
                }}
            """)
            time.sleep(1)
        except:
            pass
        
        # Extract details from the panel
        details = self._extract_job_details()
        
        return Job(
            title=title,
            company=company,
            location=job_data.get('location', details.get('location', '')),
            salary=details.get('salary', ''),
            description=details.get('description', ''),
            url=details.get('url', ''),
            platform=self.platform_name,
            date_posted=job_data.get('datePosted', details.get('date_posted', '')),
            job_type=job_data.get('jobType', '')
        )
    
    def _extract_job_details(self) -> dict:
        """Extract job details from the details panel."""
        try:
            details = self.driver.execute_script("""
                const result = {
                    description: '',
                    salary: '',
                    url: '',
                    location: '',
                    date_posted: ''
                };
                
                // Description
                const descEl = document.querySelector('.OLKT8d, .HBvzbc');
                if (descEl) {
                    result.description = descEl.innerText.substring(0, 3000);
                }
                
                // Apply link - look for links with "Apply" in aria-label or text
                const applyLinks = document.querySelectorAll('a[aria-label^="Apply"], a.nNzjpf-cS4Vcb-PvZLI-Ueh9jd-LgbsSe-Jyewjb-tlSJBe');
                for (const link of applyLinks) {
                    if (link.href && link.href.startsWith('http') && !link.href.includes('google.com/search')) {
                        result.url = link.href;
                        break;
                    }
                }
                
                // Fallback: find any link that looks like a job application
                if (!result.url) {
                    const allLinks = document.querySelectorAll('.whazf a, a[data-ved]');
                    for (const link of allLinks) {
                        const href = link.href || '';
                        if (href && !href.includes('google.com') && 
                            (href.includes('linkedin') || href.includes('indeed') || 
                             href.includes('dice') || href.includes('lever') ||
                             href.includes('greenhouse') || href.includes('workday') ||
                             href.includes('jobs') || href.includes('careers'))) {
                            result.url = href;
                            break;
                        }
                    }
                }
                
                // Salary - look for USD amounts only ($ or US$)
                const allText = document.body.innerText;
                // Match USD salary patterns: $120,000, US$150K, $80K-$120K a year
                const salaryMatch = allText.match(/(?:US)?\$[\d,]+(?:K)?(?:\s*[-–]\s*(?:US)?\$[\d,]+(?:K)?)?(?:\s*(?:a year|per year|annually|yr|\/year))?/i);
                if (salaryMatch) {
                    // Only accept if it looks like USD (no other currency symbols)
                    const salary = salaryMatch[0];
                    // Filter out non-USD currencies by checking context
                    if (!salary.includes('SGD') && !salary.includes('EUR') && 
                        !salary.includes('GBP') && !salary.includes('CAD') &&
                        !salary.includes('AUD') && !salary.includes('INR')) {
                        result.salary = salary;
                    }
                }
                
                return result;
            """)
            
            return details if details else {}
            
        except Exception as e:
            print(f"[GoogleJobs] Error extracting details: {e}")
            return {}
    
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
