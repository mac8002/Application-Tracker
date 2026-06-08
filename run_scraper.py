#!/usr/bin/env python3
"""
Simple script to run the job scraper once and create the spreadsheet.
This is useful for testing and one-time runs without the scheduler.
"""

from job_tracker import process_jobs

if __name__ == "__main__":
    print("=" * 60)
    print("QA Engineer Job Scraper - Single Run")
    print("=" * 60)
    print("This will scrape LinkedIn, Indeed, and Glassdoor for QA Engineer jobs")
    print("and create/update the job_opportunities.xlsx spreadsheet.")
    print("=" * 60)
    
    process_jobs()
    
    print("=" * 60)
    print("Scraping completed! Check job_opportunities.xlsx for results.")
    print("=" * 60)