#!/usr/bin/env python3
"""
Test email functionality with sample data
"""

import pandas as pd
from job_tracker import send_email

def test_email():
    """Test email sending with sample data"""
    try:
        # Read the spreadsheet
        df = pd.read_excel("job_opportunities.xlsx")
        
        if df.empty:
            print("No jobs found in spreadsheet. Run add_sample_data.py first.")
            return
        
        # Get the first 2 jobs as "new jobs" for testing
        new_jobs = df.head(2)
        
        print(f"Testing email with {len(new_jobs)} sample jobs...")
        print("Jobs to include in email:")
        for _, job in new_jobs.iterrows():
            print(f"- {job['Title']} at {job['Company']}")
        
        # Send test email
        send_email(new_jobs)
        
    except FileNotFoundError:
        print("Spreadsheet not found. Run add_sample_data.py first.")
    except Exception as e:
        print(f"Error testing email: {e}")

if __name__ == "__main__":
    test_email()