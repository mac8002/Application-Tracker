#!/usr/bin/env python3
"""
Add sample job data for testing purposes
"""

import pandas as pd
from datetime import datetime

# Sample job data
sample_jobs = [
    {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Title": "Senior QA Engineer",
        "Company": "TechCorp Inc",
        "Location": "Remote",
        "Link": "https://example.com/job1",
        "Source": "LinkedIn",
        "Applied": False
    },
    {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Title": "QA Automation Engineer",
        "Company": "StartupXYZ",
        "Location": "New York, NY",
        "Link": "https://example.com/job2",
        "Source": "Indeed",
        "Applied": False
    },
    {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Title": "Quality Assurance Specialist",
        "Company": "BigTech Solutions",
        "Location": "San Francisco, CA",
        "Link": "https://example.com/job3",
        "Source": "Glassdoor",
        "Applied": False
    },
    {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Title": "Manual QA Tester",
        "Company": "WebDev Agency",
        "Location": "Remote",
        "Link": "https://example.com/job4",
        "Source": "LinkedIn",
        "Applied": True
    }
]

def add_sample_data():
    """Add sample data to the spreadsheet"""
    SPREADSHEET_PATH = "job_opportunities.xlsx"
    
    try:
        # Try to read existing data
        df = pd.read_excel(SPREADSHEET_PATH)
        print(f"Found existing spreadsheet with {len(df)} jobs")
    except FileNotFoundError:
        # Create new dataframe
        df = pd.DataFrame(columns=["Date", "Title", "Company", "Location", "Link", "Source", "Applied"])
        print("Created new spreadsheet")
    
    # Add sample data
    sample_df = pd.DataFrame(sample_jobs)
    df = pd.concat([df, sample_df], ignore_index=True)
    
    # Remove duplicates
    df.drop_duplicates(subset=["Title", "Company", "Link"], keep="last", inplace=True)
    
    # Save to Excel
    df.to_excel(SPREADSHEET_PATH, index=False)
    
    print(f"Added sample data. Total jobs in spreadsheet: {len(df)}")
    print("\nSample jobs added:")
    for job in sample_jobs:
        print(f"- {job['Title']} at {job['Company']} ({job['Source']})")

if __name__ == "__main__":
    add_sample_data()