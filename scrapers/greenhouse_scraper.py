"""
Greenhouse Jobs scraper - covers 2000+ tech companies.

Companies using Greenhouse include:
- OpenAI, Anthropic, Notion, Figma, Coinbase, Discord, 
- Instacart, Cloudflare, Airbnb, DoorDash, Stripe, and many more
"""

import requests
import re
from typing import List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, Job


# Popular tech companies using Greenhouse (add more as needed)
GREENHOUSE_COMPANIES = [
    # AI/ML Companies
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic"),
    ("cohere", "Cohere"),
    ("scale", "Scale AI"),
    ("huggingface", "Hugging Face"),
    ("databricks", "Databricks"),
    ("weights-and-biases", "Weights & Biases"),
    ("anyscale", "Anyscale"),
    ("deepmind", "DeepMind"),
    
    # Big Tech / Unicorns
    ("notion", "Notion"),
    ("figma", "Figma"),
    ("discord", "Discord"),
    ("stripe", "Stripe"),
    ("coinbase", "Coinbase"),
    ("airbnb", "Airbnb"),
    ("doordash", "DoorDash"),
    ("instacart", "Instacart"),
    ("cloudflare", "Cloudflare"),
    ("datadog", "Datadog"),
    ("mongodb", "MongoDB"),
    ("elastic", "Elastic"),
    ("hashicorp", "HashiCorp"),
    ("plaid", "Plaid"),
    
    # Growing AI Startups
    ("runwayml", "Runway"),
    ("midjourney", "Midjourney"),
    ("jasperai", "Jasper AI"),
    ("replicate", "Replicate"),
]


class GreenhouseScraper(BaseScraper):
    """Scraper for Greenhouse job boards."""
    
    BASE_URL = "https://boards.greenhouse.io"
    API_URL = "https://boards-api.greenhouse.io/v1/boards"
    
    def __init__(self, headless: bool = True):
        """Initialize the Greenhouse scraper."""
        super().__init__("Greenhouse")
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
        """Search all Greenhouse companies for matching jobs."""
        all_jobs = []
        query_lower = query.lower()
        
        for company_slug, company_name in GREENHOUSE_COMPANIES:
            try:
                jobs = self._search_company(
                    company_slug, company_name, query_lower, 
                    location, remote_only, posted_within_hours
                )
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"[Greenhouse] Error searching {company_name}: {e}")
                continue
        
        return all_jobs
    
    def _search_company(
        self, 
        company_slug: str, 
        company_name: str,
        query: str,
        location: str,
        remote_only: bool,
        posted_within_hours: int
    ) -> List[Job]:
        """Search a single company's Greenhouse board."""
        jobs = []
        
        # Use Greenhouse API
        api_url = f"{self.API_URL}/{company_slug}/jobs"
        
        try:
            response = self.session.get(api_url, timeout=10)
            if response.status_code != 200:
                return jobs
            
            data = response.json()
            job_listings = data.get("jobs", [])
            
            for job_data in job_listings:
                # Check if job title matches query
                title = job_data.get("title", "").lower()
                if not self._matches_query(title, query):
                    continue
                
                # Get location
                job_location = job_data.get("location", {}).get("name", "")
                
                # Filter for remote if needed
                if remote_only:
                    loc_lower = job_location.lower()
                    if not any(x in loc_lower for x in ['remote', 'anywhere', 'distributed']):
                        # Check if US location
                        if not any(x in loc_lower for x in ['united states', 'usa', 'us', 'new york', 'san francisco', 'seattle', 'boston', 'chicago', 'austin', 'denver']):
                            continue
                
                # Get job details
                job_url = job_data.get("absolute_url", "")
                job_id = job_data.get("id", "")
                updated_at = job_data.get("updated_at", "")
                
                # Parse date
                date_posted = self._parse_date(updated_at)
                
                # Check date filter
                if posted_within_hours:
                    hours_ago = self._hours_since(updated_at)
                    if hours_ago > posted_within_hours:
                        continue
                
                # Get full description
                description = self._get_job_description(company_slug, job_id)
                
                # Extract salary from description
                salary = self._extract_salary(description)
                
                job = Job(
                    title=job_data.get("title", ""),
                    company=company_name,
                    location=job_location,
                    salary=salary,
                    description=description[:3000] if description else "",
                    url=job_url,
                    platform=f"Greenhouse ({company_name})",
                    date_posted=date_posted,
                    job_type=""
                )
                jobs.append(job)
                
        except Exception as e:
            print(f"[Greenhouse] API error for {company_name}: {e}")
        
        return jobs
    
    def _matches_query(self, title: str, query: str) -> bool:
        """Check if job title matches search query."""
        # Split query into keywords
        keywords = query.lower().split()
        title_lower = title.lower()
        
        # Match if any keyword is in title
        for keyword in keywords:
            if keyword in title_lower:
                return True
        
        # Also match common variations
        variations = {
            'ml': ['machine learning', 'ml'],
            'machine learning': ['ml', 'machine learning'],
            'ai': ['artificial intelligence', 'ai'],
            'data scientist': ['data science', 'scientist'],
            'engineer': ['developer', 'engineer'],
            'backend': ['back-end', 'backend', 'back end'],
            'devops': ['dev ops', 'devops', 'platform'],
        }
        
        for key, alts in variations.items():
            if key in query:
                for alt in alts:
                    if alt in title_lower:
                        return True
        
        return False
    
    def _get_job_description(self, company_slug: str, job_id: int) -> str:
        """Get full job description."""
        try:
            url = f"{self.API_URL}/{company_slug}/jobs/{job_id}"
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                # Remove HTML tags
                soup = BeautifulSoup(content, 'html.parser')
                return soup.get_text(separator=' ')
        except:
            pass
        return ""
    
    def _extract_salary(self, description: str) -> str:
        """Extract salary information from description."""
        if not description:
            return ""
        
        # Common salary patterns
        patterns = [
            r'\$[\d,]+(?:K)?\s*[-–]\s*\$[\d,]+(?:K)?(?:\s*(?:per year|annually|/year|yr))?',
            r'\$[\d,]+(?:K)?(?:\s*[-–]\s*\$[\d,]+(?:K)?)?(?:\s*(?:per year|annually|/year|yr))',
            r'(?:salary|compensation|pay)(?:\s*:?\s*)\$[\d,]+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def _parse_date(self, date_str: str) -> str:
        """Parse ISO date to human readable format."""
        if not date_str:
            return ""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            diff = datetime.now(dt.tzinfo) - dt
            
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
            return date_str
    
    def _hours_since(self, date_str: str) -> int:
        """Calculate hours since date."""
        if not date_str:
            return 9999
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            diff = datetime.now(dt.tzinfo) - dt
            return int(diff.total_seconds() / 3600)
        except:
            return 9999
    
    def get_job_details(self, job: Job) -> Job:
        """Get additional job details."""
        return job
    
    def close(self):
        """Close the session."""
        self.session.close()
