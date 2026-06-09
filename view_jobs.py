#!/usr/bin/env python3
"""
Simple script to view the contents of the job opportunities spreadsheet.
"""

import pandas as pd
import os
from datetime import datetime, timedelta

SPREADSHEET_PATH = "job_opportunities.xlsx"

def view_jobs():
    if not os.path.exists(SPREADSHEET_PATH):
        print(f" Spreadsheet '{SPREADSHEET_PATH}' not found.")
        print("Run the scraper first to create the spreadsheet.")
        return
    
    try:
        df = pd.read_excel(SPREADSHEET_PATH)
        
        if df.empty:
            print(" The spreadsheet is empty. Run the scraper to populate it.")
            return
        
        # Convert Date_Found to datetime for filtering
        df['Date_Found'] = pd.to_datetime(df['Date_Found'])
        
        # Filter jobs from the last 15 days
        fifteen_days_ago = datetime.now() - timedelta(days=15)
        recent_jobs = df[df['Date_Found'] >= fifteen_days_ago]
        
        if recent_jobs.empty:
            print(" No jobs found in the last 15 days.")
            print(f"Total jobs in database: {len(df)}")
            print(f"Oldest job: {df['Date_Found'].min().strftime('%Y-%m-%d')}")
            print(f"Newest job: {df['Date_Found'].max().strftime('%Y-%m-%d')}")
            return
        
        # Use recent_jobs for display
        df = recent_jobs
        
        print("=" * 80)
        print(f" JOB OPPORTUNITIES (LAST 15 DAYS) - {len(df)} jobs found")
        print("=" * 80)
        
        # Display summary by source
        print("\n SUMMARY BY SOURCE:")
        source_counts = df['Source'].value_counts()
        for source, count in source_counts.items():
            print(f"  {source}: {count} jobs")
        
        print(f"\n DATE RANGE (LAST 15 DAYS):")
        print(f"  From: {fifteen_days_ago.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        print(f"  First job found: {df['Date_Found'].min().strftime('%Y-%m-%d')}")
        print(f"  Last job found: {df['Date_Found'].max().strftime('%Y-%m-%d')}")
        
        print("\n" + "=" * 80)
        print(" ALL JOBS:")
        print("=" * 80)
        
        # Display all jobs with formatting
        for idx, (_, job) in enumerate(df.iterrows(), 1):
            print(f"\n{idx}. {job['Title']}")
            print(f"    Company: {job['Company']}")
            print(f"    Location: {job['Location']}")
            print(f"    Source: {job['Source']}")
            print(f"    Found: {job['Date_Found'].strftime('%Y-%m-%d')}")
            print(f"    Posted: {job['Posting_Date']}")
            print(f"    Link: {job['Link']}")
        
        print("\n" + "=" * 80)
        print(f"Total: {len(df)} job opportunities")
        print("=" * 80)
        
    except Exception as e:
        print(f" Error reading spreadsheet: {e}")

if __name__ == "__main__":
    view_jobs()