#!/usr/bin/env python3
"""
Test script for job_tracker.py
This script tests individual functions without running the full automation
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_tracker import init_spreadsheet, scrape_jobs, save_to_spreadsheet

def test_environment():
    """Test if environment variables are loaded correctly"""
    from dotenv import load_dotenv
    load_dotenv()
    
    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    
    print("=== Environment Test ===")
    print(f"EMAIL_ADDRESS: {'✓ Set' if email_address else '✗ Not set'}")
    print(f"EMAIL_PASSWORD: {'✓ Set' if email_password else '✗ Not set'}")
    print(f"RECIPIENT_EMAIL: {'✓ Set' if recipient_email else '✗ Not set'}")
    print()

def test_spreadsheet():
    """Test spreadsheet initialization"""
    print("=== Spreadsheet Test ===")
    try:
        df = init_spreadsheet()
        print(f"✓ Spreadsheet initialized successfully")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Rows: {len(df)}")
    except Exception as e:
        print(f"✗ Spreadsheet initialization failed: {e}")
    print()

def test_scraping_basic():
    """Test basic scraping functionality (without actually scraping)"""
    print("=== Basic Scraping Test ===")
    print("Note: This will attempt to scrape LinkedIn. It may take a while...")
    print("Press Ctrl+C to cancel if needed.")
    
    try:
        jobs = scrape_jobs()
        print(f"✓ Scraping completed")
        print(f"  Jobs found: {len(jobs)}")
        
        if jobs:
            print("  Sample job:")
            sample_job = jobs[0]
            for key, value in sample_job.items():
                print(f"    {key}: {value}")
    except KeyboardInterrupt:
        print("✗ Scraping cancelled by user")
    except Exception as e:
        print(f"✗ Scraping failed: {e}")
    print()

if __name__ == "__main__":
    print(f"Job Tracker Test Suite - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    test_environment()
    test_spreadsheet()
    
    # Ask user if they want to test scraping
    response = input("Do you want to test scraping? (y/N): ").lower().strip()
    if response in ['y', 'yes']:
        test_scraping_basic()
    else:
        print("Skipping scraping test.")
    
    print("Test suite completed!")