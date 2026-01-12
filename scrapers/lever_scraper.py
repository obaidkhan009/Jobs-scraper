"""
Async Lever Jobs scraper with parallel API calls.

Optimized for scraping 80+ companies in parallel using aiohttp.
"""

import asyncio
import aiohttp
import re
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, Job
from config.fortune500_companies import LEVER_FORTUNE_500


class AsyncLeverScraper(BaseScraper):
    """Async scraper for Lever job boards with parallel requests."""
    
    BASE_URL = "https://jobs.lever.co"
    MAX_CONCURRENT = 50  # Max parallel requests
    TIMEOUT = 30  # Request timeout in seconds
    
    def __init__(self, headless: bool = True):
        """Initialize the async Lever scraper."""
        super().__init__("Lever")
        self.companies = LEVER_FORTUNE_500
    
    def search(
        self,
        query: str,
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> List[Job]:
        """
        Search all Lever companies for matching jobs.
        Uses asyncio for parallel API calls.
        """
        print(f"[Lever] Searching {len(self.companies)} companies in parallel...")
        
        # Run async search
        jobs = asyncio.run(self._async_search_all(
            query, location, remote_only, posted_within_hours
        ))
        
        print(f"[Lever] ✓ Found {len(jobs)} total jobs")
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
                    remote_only
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
                    pass  # Skip failed requests silently
        
        return all_jobs
    
    async def _search_company_async(
        self,
        session: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
        company_slug: str,
        company_name: str,
        query: str,
        remote_only: bool
    ) -> List[Job]:
        """Search a single company's Lever page asynchronously."""
        async with semaphore:
            jobs = []
            url = f"{self.BASE_URL}/{company_slug}?mode=json"
            
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        return jobs
                    
                    job_listings = await response.json()
                    
                    for job_data in job_listings:
                        # Check if title matches query
                        title = job_data.get("text", "").lower()
                        if not self._matches_query(title, query):
                            continue
                        
                        # Get location
                        categories = job_data.get("categories", {})
                        job_location = categories.get("location", "")
                        
                        # Filter for remote if needed
                        if remote_only:
                            loc_lower = job_location.lower() if job_location else ""
                            # Only allow jobs that explicitly mention remote
                            if not any(x in loc_lower for x in ['remote', 'anywhere', 'distributed', 'work from home', 'wfh']):
                                continue
                        
                        # Get job URL
                        job_url = job_data.get("hostedUrl", "")
                        
                        # Parse created date
                        created_at = job_data.get("createdAt", 0)
                        date_posted = self._parse_timestamp(created_at)
                        
                        job = Job(
                            title=job_data.get("text", ""),
                            company=company_name,
                            location=job_location or "Remote",
                            salary="",  # Would need to parse from description
                            description="",  # Skip for speed
                            url=job_url,
                            platform=f"Lever ({company_name})",
                            date_posted=date_posted,
                            job_type=categories.get("commitment", "")
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
        """Close the scraper (no resources to clean up)."""
        pass


# Backward compatibility alias
LeverScraper = AsyncLeverScraper
