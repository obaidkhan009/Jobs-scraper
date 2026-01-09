"""
Lever Jobs scraper - covers 1500+ tech companies.

Companies using Lever include:
- Netflix, Shopify, Lyft, Twitch, Robinhood, Unity,
- Flexport, Loom, Webflow, Deel, and many more
"""

import requests
import re
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, Job


# Popular tech companies using Lever (add more as needed)
LEVER_COMPANIES = [
    # Big Tech / Unicorns
    ("netflix", "Netflix"),
    ("shopify", "Shopify"),
    ("lyft", "Lyft"),
    ("twitch", "Twitch"),
    ("roblox", "Roblox"),
    ("unity", "Unity"),
    ("robinhood", "Robinhood"),
    ("affirm", "Affirm"),
    ("opendoor", "Opendoor"),
    
    # Growing Tech Companies
    ("flexport", "Flexport"),
    ("loom", "Loom"),
    ("webflow", "Webflow"),
    ("deel", "Deel"),
    ("retool", "Retool"),
    ("postman", "Postman"),
    ("miro", "Miro"),
    ("airtable", "Airtable"),
    ("amplitude", "Amplitude"),
    
    # AI/ML Companies
    ("perplexity", "Perplexity"),
    ("character", "Character.AI"),
    ("stability", "Stability AI"),
    ("adept", "Adept"),
    ("inflection", "Inflection AI"),
    
    # Cloud/Infra
    ("tailscale", "Tailscale"),
    ("vercel", "Vercel"),
    ("supabase", "Supabase"),
    ("planetscale", "PlanetScale"),
    ("railway", "Railway"),
]


class LeverScraper(BaseScraper):
    """Scraper for Lever job boards."""
    
    BASE_URL = "https://jobs.lever.co"
    
    def __init__(self, headless: bool = True):
        """Initialize the Lever scraper."""
        super().__init__("Lever")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def search(
        self,
        query: str,
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> List[Job]:
        """Search all Lever companies for matching jobs."""
        all_jobs = []
        query_lower = query.lower()
        
        for company_slug, company_name in LEVER_COMPANIES:
            try:
                jobs = self._search_company(
                    company_slug, company_name, query_lower,
                    location, remote_only
                )
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"[Lever] Error searching {company_name}: {e}")
                continue
        
        return all_jobs
    
    def _search_company(
        self,
        company_slug: str,
        company_name: str,
        query: str,
        location: str,
        remote_only: bool
    ) -> List[Job]:
        """Search a single company's Lever page."""
        jobs = []
        
        # Lever uses JSON API
        url = f"{self.BASE_URL}/{company_slug}?mode=json"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return jobs
            
            job_listings = response.json()
            
            for job_data in job_listings:
                # Check if title matches query
                title = job_data.get("text", "").lower()
                if not self._matches_query(title, query):
                    continue
                
                # Get location
                categories = job_data.get("categories", {})
                job_location = categories.get("location", "")
                
                # Filter for remote/US if needed
                if remote_only:
                    loc_lower = job_location.lower() if job_location else ""
                    is_remote = any(x in loc_lower for x in ['remote', 'anywhere', 'distributed', 'work from home'])
                    is_us = any(x in loc_lower for x in ['united states', 'usa', 'us', 'new york', 'san francisco', 'seattle', 'boston', 'chicago', 'austin', 'denver', 'los angeles'])
                    
                    if not is_remote and not is_us:
                        continue
                
                # Get job URL
                job_url = job_data.get("hostedUrl", "")
                
                # Get description
                description_html = job_data.get("descriptionPlain", "") or job_data.get("description", "")
                if description_html:
                    soup = BeautifulSoup(description_html, 'html.parser')
                    description = soup.get_text(separator=' ')
                else:
                    description = ""
                
                # Extract salary
                salary = self._extract_salary(description)
                
                # Get additional info
                additional = job_data.get("additional", "")
                
                # Parse created date
                created_at = job_data.get("createdAt", 0)
                date_posted = self._parse_timestamp(created_at)
                
                job = Job(
                    title=job_data.get("text", ""),
                    company=company_name,
                    location=job_location or "Remote",
                    salary=salary,
                    description=description[:3000] if description else "",
                    url=job_url,
                    platform=f"Lever ({company_name})",
                    date_posted=date_posted,
                    job_type=categories.get("commitment", "")
                )
                jobs.append(job)
                
        except Exception as e:
            print(f"[Lever] Error fetching {company_name}: {e}")
        
        return jobs
    
    def _matches_query(self, title: str, query: str) -> bool:
        """Check if job title matches search query."""
        keywords = query.lower().split()
        title_lower = title.lower()
        
        for keyword in keywords:
            if keyword in title_lower:
                return True
        
        # Match common variations
        variations = {
            'ml': ['machine learning', 'ml'],
            'machine learning': ['ml', 'machine learning'],
            'ai': ['artificial intelligence', 'ai'],
            'data scientist': ['data science', 'scientist'],
            'engineer': ['developer', 'engineer'],
            'backend': ['back-end', 'backend', 'back end'],
            'devops': ['dev ops', 'devops', 'platform', 'sre'],
        }
        
        for key, alts in variations.items():
            if key in query:
                for alt in alts:
                    if alt in title_lower:
                        return True
        
        return False
    
    def _extract_salary(self, description: str) -> str:
        """Extract salary from description."""
        if not description:
            return ""
        
        patterns = [
            r'\$[\d,]+(?:K)?\s*[-–]\s*\$[\d,]+(?:K)?(?:\s*(?:per year|annually|/year|yr))?',
            r'\$[\d,]+(?:K)?(?:\s*[-–]\s*\$[\d,]+(?:K)?)?(?:\s*(?:per year|annually|/year|yr))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def _parse_timestamp(self, timestamp: int) -> str:
        """Parse Unix timestamp to human readable format."""
        if not timestamp:
            return ""
        try:
            # Lever uses milliseconds
            dt = datetime.fromtimestamp(timestamp / 1000)
            diff = datetime.now() - dt
            
            if diff.days == 0:
                hours = diff.seconds // 3600
                if hours == 0:
                    return "Just now"
                return f"{hours} hours ago"
            elif diff.days == 1:
                return "1 day ago"
            else:
                return f"{diff.days} days ago"
        except:
            return ""
    
    def get_job_details(self, job: Job) -> Job:
        """Get additional job details."""
        return job
    
    def close(self):
        """Close the session."""
        self.session.close()
