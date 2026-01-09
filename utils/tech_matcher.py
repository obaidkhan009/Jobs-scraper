"""
Tech stack matcher for scoring jobs based on good/bad technologies.
"""

import re
from typing import List, Tuple, Set
from scrapers.base_scraper import Job
from config.tech_stacks import GOOD_TECH, BAD_TECH, MAX_BAD_TECH_COUNT


class TechMatcher:
    """Scores jobs based on matching good and bad technologies."""
    
    def __init__(
        self, 
        good_tech: List[str] = None, 
        bad_tech: List[str] = None,
        max_bad_tech: int = None
    ):
        """
        Initialize the tech matcher.
        
        Args:
            good_tech: List of desired technologies
            bad_tech: List of technologies to avoid
            max_bad_tech: Maximum allowed bad tech matches before filtering
        """
        self.good_tech = good_tech or GOOD_TECH
        self.bad_tech = bad_tech or BAD_TECH
        self.max_bad_tech = max_bad_tech or MAX_BAD_TECH_COUNT
        
        # Precompile regex patterns for faster matching
        self._good_patterns = self._compile_patterns(self.good_tech)
        self._bad_patterns = self._compile_patterns(self.bad_tech)
    
    def _compile_patterns(self, tech_list: List[str]) -> List[Tuple[str, re.Pattern]]:
        """
        Compile regex patterns for each technology.
        Uses word boundaries to avoid partial matches.
        """
        patterns = []
        for tech in tech_list:
            # Escape special regex characters
            escaped = re.escape(tech)
            # Create pattern with word boundaries (case insensitive)
            # Handle special cases like "C#", ".NET", etc.
            pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
            patterns.append((tech, pattern))
        return patterns
    
    def find_matches(self, text: str, patterns: List[Tuple[str, re.Pattern]]) -> Set[str]:
        """
        Find all matching technologies in the given text.
        
        Args:
            text: The text to search (job description, title, etc.)
            patterns: List of (tech_name, compiled_pattern) tuples
            
        Returns:
            Set of matched technology names
        """
        matches = set()
        for tech_name, pattern in patterns:
            if pattern.search(text):
                matches.add(tech_name)
        return matches
    
    def score_job(self, job: Job) -> Job:
        """
        Score a job based on tech stack matches.
        
        Updates the job object in place with:
        - good_tech_found: List of matching good technologies
        - bad_tech_found: List of matching bad technologies  
        - score: Calculated score (higher is better)
        
        Args:
            job: Job object to score
            
        Returns:
            The updated job object
        """
        # Combine all searchable text
        search_text = f"{job.title} {job.company} {job.description} {job.location}"
        
        # Find matches
        good_matches = self.find_matches(search_text, self._good_patterns)
        bad_matches = self.find_matches(search_text, self._bad_patterns)
        
        # Calculate score
        # Good tech adds points, bad tech subtracts (with higher penalty)
        good_score = len(good_matches) * 10
        bad_score = len(bad_matches) * 15  # Higher penalty for bad tech
        
        score = max(0, good_score - bad_score + 50)  # Base score of 50
        
        # Bonus for having many good tech matches
        if len(good_matches) >= 5:
            score += 20
        if len(good_matches) >= 10:
            score += 30
        
        # Update job object
        job.good_tech_found = sorted(list(good_matches))
        job.bad_tech_found = sorted(list(bad_matches))
        job.score = score
        
        return job
    
    def filter_jobs(self, jobs: List[Job]) -> List[Job]:
        """
        Filter and score a list of jobs.
        
        Removes jobs that have too many bad tech matches.
        
        Args:
            jobs: List of Job objects to filter
            
        Returns:
            Filtered and scored list of jobs
        """
        scored_jobs = []
        
        for job in jobs:
            # Score the job
            self.score_job(job)
            
            # Filter out jobs with too many bad tech matches
            if len(job.bad_tech_found) <= self.max_bad_tech:
                scored_jobs.append(job)
            else:
                print(f"[TechMatcher] Filtered out: {job.title} at {job.company} "
                      f"(bad tech: {len(job.bad_tech_found)} > {self.max_bad_tech})")
        
        # Sort by score (highest first)
        scored_jobs.sort(key=lambda j: j.score, reverse=True)
        
        return scored_jobs
    
    def get_match_summary(self, job: Job) -> str:
        """Get a human-readable summary of tech matches for a job."""
        good = ", ".join(job.good_tech_found[:5])
        if len(job.good_tech_found) > 5:
            good += f" (+{len(job.good_tech_found) - 5} more)"
        
        bad = ", ".join(job.bad_tech_found) if job.bad_tech_found else "None"
        
        return f"Good: [{good}] | Bad: [{bad}] | Score: {job.score}"
