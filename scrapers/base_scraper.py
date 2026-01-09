"""
Base scraper interface and common data models for job scrapers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Job:
    """Represents a job listing."""
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    description: str = ""
    url: str = ""
    direct_apply_url: Optional[str] = None
    platform: str = ""
    date_posted: Optional[str] = None
    job_type: Optional[str] = None  # Full-time, Part-time, Contract
    
    # Tech matching results (populated by TechMatcher)
    good_tech_found: List[str] = field(default_factory=list)
    bad_tech_found: List[str] = field(default_factory=list)
    score: int = 0
    
    # Metadata
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def __hash__(self):
        """Hash based on company and title for deduplication."""
        return hash((self.company.lower().strip(), self.title.lower().strip()))
    
    def __eq__(self, other):
        """Two jobs are equal if same company and title."""
        if not isinstance(other, Job):
            return False
        return (
            self.company.lower().strip() == other.company.lower().strip() and
            self.title.lower().strip() == other.title.lower().strip()
        )


class BaseScraper(ABC):
    """Abstract base class for job scrapers."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    @abstractmethod
    def search(
        self,
        query: str,
        location: str = "United States",
        remote_only: bool = True,
        posted_within_hours: int = 48
    ) -> List[Job]:
        """
        Search for jobs matching the query.
        
        Args:
            query: Job title or keywords to search for
            location: Location filter (e.g., "United States")
            remote_only: If True, only return remote jobs
            posted_within_hours: Only return jobs posted within this many hours
            
        Returns:
            List of Job objects
        """
        pass
    
    @abstractmethod
    def get_job_details(self, job: Job) -> Job:
        """
        Fetch full job details including description.
        
        Args:
            job: Job object with at least the URL populated
            
        Returns:
            Job object with full details
        """
        pass
    
    def close(self):
        """Clean up resources. Override in subclasses if needed."""
        pass
