"""
Async Greenhouse Jobs scraper with parallel API calls.

Optimized for scraping 200+ companies in parallel using aiohttp.
Covers Fortune 500, AI/ML companies, and high-growth startups.
"""

import asyncio
import aiohttp
import re
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, Job
from config.fortune500_companies import GREENHOUSE_FORTUNE_500


class AsyncGreenhouseScraper(BaseScraper):
    """Async scraper for Greenhouse job boards with parallel requests."""
    
    API_URL = "https://boards-api.greenhouse.io/v1/boards"
    MAX_CONCURRENT = 50  # Max parallel requests
    TIMEOUT = 30  # Request timeout in seconds
    
    def __init__(self, headless: bool = True):
        """Initialize the async Greenhouse scraper."""
        super().__init__("Greenhouse")
        self.companies = GREENHOUSE_FORTUNE_500
    
    def search(
        self,
        query: str,
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> List[Job]:
        """
        Search all Greenhouse companies for matching jobs.
        Uses asyncio for parallel API calls.
        """
        print(f"[Greenhouse] Searching {len(self.companies)} companies in parallel...")
        
        # Run async search
        jobs = asyncio.run(self._async_search_all(
            query, location, remote_only, posted_within_hours
        ))
        
        print(f"[Greenhouse] ✓ Found {len(jobs)} total jobs")
        return jobs
    
    async def _async_search_all(
        self,
        query: str,
        location: str,
        remote_only: bool,
        posted_within_hours: int
    ) -> List[Job]:
        """Search all companies asynchronously."""
        all_jobs = []
        query_lower = query.lower()
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        
        # Create timeout for requests
        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Create tasks for all companies
            tasks = [
                self._search_company_async(
                    session, semaphore, slug, name, query_lower,
                    remote_only, posted_within_hours
                )
                for slug, name in self.companies
            ]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful results
            for result in results:
                if isinstance(result, list):
                    all_jobs.extend(result)
                elif isinstance(result, Exception):
                    # Silently skip failed requests
                    pass
        
        return all_jobs
    
    async def _search_company_async(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        company_slug: str,
        company_name: str,
        query: str,
        remote_only: bool,
        posted_within_hours: int
    ) -> List[Job]:
        """Search a single company's Greenhouse board asynchronously."""
        async with semaphore:
            jobs = []
            api_url = f"{self.API_URL}/{company_slug}/jobs"
            
            try:
                async with session.get(api_url) as response:
                    if response.status != 200:
                        return jobs
                    
                    data = await response.json()
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
                            # Only allow jobs that explicitly mention remote
                            if not any(x in loc_lower for x in ['remote', 'anywhere', 'distributed', 'work from home', 'wfh']):
                                continue
                        
                        # Get job details
                        job_url = job_data.get("absolute_url", "")
                        updated_at = job_data.get("updated_at", "")
                        
                        # Parse date
                        date_posted = self._parse_date(updated_at)
                        
                        # Check date filter
                        if posted_within_hours:
                            hours_ago = self._hours_since(updated_at)
                            if hours_ago > posted_within_hours:
                                continue
                        
                        # Create job object (skip full description for speed)
                        job = Job(
                            title=job_data.get("title", ""),
                            company=company_name,
                            location=job_location,
                            salary="",  # Would need separate API call
                            description="",  # Would need separate API call
                            url=job_url,
                            platform=f"Greenhouse ({company_name})",
                            date_posted=date_posted,
                            job_type=""
                        )
                        jobs.append(job)
                        
            except asyncio.TimeoutError:
                pass  # Skip timed out requests
            except Exception as e:
                pass  # Skip failed requests
            
            return jobs
    
    def _matches_query(self, title: str, query: str) -> bool:
        """Check if job title matches search query."""
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
            return 0  # Empty date = assume recent
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            diff = datetime.now(dt.tzinfo) - dt
            return int(diff.total_seconds() / 3600)
        except:
            return 0  # Parse error = assume recent
    
    def get_job_details(self, job: Job) -> Job:
        """Get additional job details."""
        return job
    
    def close(self):
        """Close the scraper (no resources to clean up)."""
        pass


# Backward compatibility alias
GreenhouseScraper = AsyncGreenhouseScraper
