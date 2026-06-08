#!/usr/bin/env python3
"""
Script to view ALL jobs in the spreadsheet (no date filtering).
"""

import pandas as pd
import os
from datetime import datetime

SPREADSHEET_PATH = "job_opportunities.xlsx"

def view_all_jobs():
    if not os.path.exists(SPREADSHEET_PATH):
        print(f"❌ Spreadsheet '{SPREADSHEET_PATH}' not found.")
        print("Run the scraper first to create the spreadsheet.")
        return
    
    try:
        df = pd.read_excel(SPREADSHEET_PATH)
        
        if df.empty:
            print("📋 The spreadsheet is empty. Run the scraper to populate it.")
            return
        
        # Convert Date_Found to datetime for proper formatting
        df['Date_Found'] = pd.to_datetime(df['Date_Found'])
        
        print("=" * 80)
        print(f"📊 ALL JOB OPPORTUNITIES - {len(df)} jobs found")
        print("=" * 80)
        
        # Display summary by source
        print("\n📈 SUMMARY BY SOURCE:")
        source_counts = df['Source'].value_counts()
        for source, count in source_counts.items():
            print(f"  {source}: {count} jobs")
        
        print(f"\n📅 FULL DATE RANGE:")
        print(f"  First job found: {df['Date_Found'].min().strftime('%Y-%m-%d')}")
        print(f"  Last job found: {df['Date_Found'].max().strftime('%Y-%m-%d')}")
        
        # Show jobs by date (most recent first)
        df_sorted = df.sort_values('Date_Found', ascending=False)
        
        print("\n" + "=" * 80)
        print("📋 ALL JOBS (MOST RECENT FIRST):")
        print("=" * 80)
        
        # Display all jobs with formatting
        for idx, (_, job) in enumerate(df_sorted.iterrows(), 1):
            print(f"\n{idx}. {job['Title']}")
            print(f"   🏢 Company: {job['Company']}")
            print(f"   📍 Location: {job['Location']}")
            print(f"   🌐 Source: {job['Source']}")
            print(f"   📅 Found: {job['Date_Found'].strftime('%Y-%m-%d')}")
            print(f"   📆 Posted: {job['Posting_Date']}")
            print(f"   🔗 Link: {job['Link']}")
        
        print("\n" + "=" * 80)
        print(f"Total: {len(df)} job opportunities")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error reading spreadsheet: {e}")

if __name__ == "__main__":
    view_all_jobs()