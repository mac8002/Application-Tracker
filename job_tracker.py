import time
import schedule
import smtplib
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configuration
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
SPREADSHEET_PATH = "job_opportunities.xlsx"
JOB_BOARDS = {
    "LinkedIn": "https://www.linkedin.com/jobs/search/?keywords=QA%20Engineer&location=Remote",
    "Indeed": "https://www.indeed.com/jobs?q=QA+Engineer&l=Remote",
    "Glassdoor": "https://www.glassdoor.com/Job/remote-qa-engineer-jobs-SRCH_IL.0,6_IC1154532_KO7,18.htm"
}

# Initialize spreadsheet
def init_spreadsheet():
    try:
        df = pd.read_excel(SPREADSHEET_PATH)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Date_Found", "Title", "Company", "Location", "Link", "Source", "Posting_Date"])
        df.to_excel(SPREADSHEET_PATH, index=False)
    return df

# Process job board specific scraping
def process_job_board(soup, source):
    """Process job listings from different job boards"""
    jobs = []
    
    if source == "LinkedIn":
        # Updated selectors for current LinkedIn structure
        job_cards = soup.select("[data-testid='job-search-result']")
        if not job_cards:
            # Fallback selectors
            job_cards = soup.select(".jobs-search-results__list-item, .job-search-card")
        
        print(f"Found {len(job_cards)} job cards on {source}")
        
        for card in job_cards[:10]:  # Limit to 10
            try:
                # Try multiple selector patterns for title
                title_elem = (card.select_one(".job-card-list__title a") or 
                            card.select_one(".job-card-list__title") or
                            card.select_one("[data-testid='job-title']") or
                            card.select_one("h3 a") or
                            card.select_one(".base-search-card__title"))
                
                # Try multiple selector patterns for company
                company_elem = (card.select_one(".job-card-container__company-name") or
                              card.select_one("[data-testid='job-search-card-subtitle']") or
                              card.select_one(".base-search-card__subtitle") or
                              card.select_one("h4 a"))
                
                # Try multiple selector patterns for location
                location_elem = (card.select_one(".job-card-container__metadata-item") or
                               card.select_one("[data-testid='job-search-card-location']") or
                               card.select_one(".job-search-card__location"))
                
                # Try to get posting date
                date_elem = (card.select_one("time") or
                           card.select_one(".job-search-card__listdate") or
                           card.select_one("[data-testid='job-search-card-date']"))
                
                # Get link
                link_elem = (card.select_one(".job-card-list__title a") or
                           card.select_one("h3 a") or
                           card.select_one(".base-search-card__title a"))
                
                if title_elem and company_elem:
                    title_text = title_elem.get_text(strip=True)
                    company_text = company_elem.get_text(strip=True)
                    location_text = location_elem.get_text(strip=True) if location_elem else "N/A"
                    
                    # Extract posting date
                    posting_date = "N/A"
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        # Try to get datetime attribute if available
                        if date_elem.get("datetime"):
                            posting_date = date_elem["datetime"]
                        else:
                            posting_date = date_text
                    
                    # Handle link extraction
                    link_url = ""
                    if link_elem and link_elem.get("href"):
                        link_url = link_elem["href"]
                        if link_url.startswith("/"):
                            link_url = "https://www.linkedin.com" + link_url
                    
                    jobs.append({
                        "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title_text,
                        "Company": company_text,
                        "Location": location_text,
                        "Link": link_url,
                        "Source": source,
                        "Posting_Date": posting_date
                    })
                    print(f"Scraped: {title_text} at {company_text}")
            
            except Exception as e:
                print(f"Error processing job card: {e}")
                continue
    
    elif source == "Indeed":
        # Indeed job scraping
        job_cards = soup.select("[data-jk]")  # Indeed uses data-jk attribute
        if not job_cards:
            job_cards = soup.select(".job_seen_beacon")
        
        print(f"Found {len(job_cards)} job cards on {source}")
        
        for card in job_cards[:10]:
            try:
                title_elem = card.select_one("h2 a span") or card.select_one(".jobTitle a")
                company_elem = card.select_one(".companyName") or card.select_one("[data-testid='company-name']")
                location_elem = card.select_one("[data-testid='job-location']") or card.select_one(".companyLocation")
                date_elem = card.select_one(".date") or card.select_one("[data-testid='job-age']")
                link_elem = card.select_one("h2 a") or card.select_one(".jobTitle a")
                
                if title_elem and company_elem:
                    title_text = title_elem.get_text(strip=True)
                    company_text = company_elem.get_text(strip=True)
                    location_text = location_elem.get_text(strip=True) if location_elem else "N/A"
                    
                    # Extract posting date
                    posting_date = "N/A"
                    if date_elem:
                        posting_date = date_elem.get_text(strip=True)
                    
                    link_url = ""
                    if link_elem and link_elem.get("href"):
                        link_url = link_elem["href"]
                        if link_url.startswith("/"):
                            link_url = "https://www.indeed.com" + link_url
                    
                    jobs.append({
                        "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title_text,
                        "Company": company_text,
                        "Location": location_text,
                        "Link": link_url,
                        "Source": source,
                        "Posting_Date": posting_date
                    })
                    print(f"Scraped: {title_text} at {company_text}")
            
            except Exception as e:
                print(f"Error processing Indeed job card: {e}")
                continue
    
    elif source == "Glassdoor":
        # Glassdoor job scraping
        job_cards = soup.select("[data-test='job-listing']") or soup.select(".react-job-listing")
        
        print(f"Found {len(job_cards)} job cards on {source}")
        
        for card in job_cards[:10]:
            try:
                title_elem = card.select_one("[data-test='job-title']") or card.select_one(".jobTitle")
                company_elem = card.select_one("[data-test='employer-name']") or card.select_one(".employerName")
                location_elem = card.select_one("[data-test='job-location']") or card.select_one(".location")
                date_elem = card.select_one("[data-test='job-age']") or card.select_one(".jobAge")
                link_elem = card.select_one("[data-test='job-title'] a") or card.select_one(".jobTitle a")
                
                if title_elem and company_elem:
                    title_text = title_elem.get_text(strip=True)
                    company_text = company_elem.get_text(strip=True)
                    location_text = location_elem.get_text(strip=True) if location_elem else "N/A"
                    
                    # Extract posting date
                    posting_date = "N/A"
                    if date_elem:
                        posting_date = date_elem.get_text(strip=True)
                    
                    link_url = ""
                    if link_elem and link_elem.get("href"):
                        link_url = link_elem["href"]
                        if link_url.startswith("/"):
                            link_url = "https://www.glassdoor.com" + link_url
                    
                    jobs.append({
                        "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title_text,
                        "Company": company_text,
                        "Location": location_text,
                        "Link": link_url,
                        "Source": source,
                        "Posting_Date": posting_date
                    })
                    print(f"Scraped: {title_text} at {company_text}")
            
            except Exception as e:
                print(f"Error processing Glassdoor job card: {e}")
                continue
    
    return jobs

# Scrape job listings
def scrape_jobs():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    jobs = []

    try:
        for source, url in JOB_BOARDS.items():
            print(f"Scraping {source}...")
            driver.get(url)
            time.sleep(5)  # Wait for page load
            
            # Wait for job listings to load (different selectors for different sites)
            try:
                if source == "LinkedIn":
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-search-result'], .jobs-search-results__list-item"))
                    )
                elif source == "Indeed":
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-jk], .job_seen_beacon"))
                    )
                elif source == "Glassdoor":
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='job-listing'], .react-job-listing"))
                    )
            except Exception as e:
                print(f"Failed to load job listings from {source}: {e}")
                print("Continuing with available page content...")
                # Don't skip, try to scrape what's available
            
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Process different job boards
            jobs_found = process_job_board(soup, source)
            jobs.extend(jobs_found)

    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        driver.quit()

    print(f"Total jobs scraped: {len(jobs)}")
    return jobs

# Save jobs to spreadsheet
def save_to_spreadsheet(jobs):
    df = init_spreadsheet()
    new_jobs_df = pd.DataFrame(jobs)
    existing_keys = set(zip(df["Title"], df["Company"], df["Link"]))
    truly_new = new_jobs_df[
        ~new_jobs_df.apply(lambda r: (r["Title"], r["Company"], r["Link"]) in existing_keys, axis=1)
    ]
    df = pd.concat([df, truly_new], ignore_index=True)
    df.to_excel(SPREADSHEET_PATH, index=False)
    return truly_new



# Send email notification
def send_email(new_jobs):
    if new_jobs.empty:
        print("No new jobs to email about.")
        return

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD or not RECIPIENT_EMAIL:
        print("Email configuration missing. Please check your .env file.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = f"Daily QA Engineer Job Tracker Update - {len(new_jobs)} New Jobs Found"

        body = f"Found {len(new_jobs)} new QA Engineer job opportunities:\n\n"
        for i, (_, job) in enumerate(new_jobs.iterrows(), 1):
            body += f"{i}. Title: {job['Title']}\n"
            body += f"   Company: {job['Company']}\n"
            body += f"   Location: {job['Location']}\n"
            body += f"   Link: {job['Link']}\n"
            body += f"   Source: {job['Source']}\n"
            body += f"   Date Found: {job['Date_Found']}\n"
            body += f"   Posting Date: {job['Posting_Date']}\n\n"
        
        body += f"\nTotal jobs in database: {len(pd.read_excel(SPREADSHEET_PATH))}\n"
        body += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"✓ Email notification sent successfully to {RECIPIENT_EMAIL}")
            
    except smtplib.SMTPAuthenticationError:
        print("✗ Email authentication failed. Please check your email credentials.")
        print("Note: For Gmail, you may need to use an App Password instead of your regular password.")
    except smtplib.SMTPException as e:
        print(f"✗ SMTP error occurred: {e}")
    except Exception as e:
        print(f"✗ Error sending email: {e}")

# Main job processing function
def process_jobs():
    print(f"=== Job Tracker Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    try:
        print(" Scraping job boards for QA Engineer jobs...")
        jobs = scrape_jobs()
        
        if not jobs:
            print("  No jobs found during scraping.")
            return
        
        print(f" Saving {len(jobs)} jobs to spreadsheet...")
        new_jobs = save_to_spreadsheet(jobs)
        
        if not new_jobs.empty:
            print(f" Found {len(new_jobs)} new jobs!")
            
            print(" Sending email notification...")
            send_email(new_jobs)
        else:
            print("ℹ  No new QA Engineer jobs found (all jobs already in database).")
            
    except Exception as e:
        print(f" Error in main process: {e}")
    
    print(f"=== Job Tracker Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

# Schedule daily task
schedule.every().day.at("09:00").do(process_jobs)

# Run scheduler
if __name__ == "__main__":
    print("QA Engineer Job Tracker started...")
    print("This script will scrape job boards and create a comprehensive spreadsheet with job details.")
    process_jobs()  # Run immediately for testing
    while True:
        schedule.run_pending()
        time.sleep(60)