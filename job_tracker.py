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
import re
from urllib.parse import urlsplit, urlunsplit

# Load environment variables from .env file
load_dotenv()

# Configuration
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
SPREADSHEET_PATH = "job_opportunities.xlsx"
CHROME_PROFILE_PATH = os.path.abspath("chrome_profile")
MANUAL_VERIFICATION_TIMEOUT_SECONDS = 300
DISABLED_JOB_BOARDS = {"Glassdoor"}
MANUAL_VERIFICATION_JOB_BOARDS = {"Indeed"}

# Each source can have multiple URLs (e.g. one for US, one for Canada,
# and one per job title we search for). scrape_jobs() loops through every
# URL for every source.
JOB_BOARDS = {
    "LinkedIn": [
        "https://www.linkedin.com/jobs/search/?keywords=QA%20Engineer&location=United%20States&geoId=103644278",
        "https://www.linkedin.com/jobs/search/?keywords=QA%20Engineer&location=Canada&geoId=101174742",
        "https://www.linkedin.com/jobs/search/?keywords=QA%20Analyst&location=United%20States&geoId=103644278",
        "https://www.linkedin.com/jobs/search/?keywords=QA%20Analyst&location=Canada&geoId=101174742"
    ],
    "Indeed": [
        "https://www.indeed.com/jobs?q=QA+Engineer&l=United+States",
        "https://ca.indeed.com/jobs?q=QA+Engineer&l=Canada",
        "https://www.indeed.com/jobs?q=QA+Analyst&l=United+States",
        "https://ca.indeed.com/jobs?q=QA+Analyst&l=Canada"
    ],
    "Glassdoor": [
        "https://www.glassdoor.com/Job/united-states-qa-engineer-jobs-SRCH_IL.0,13_IN1_KO14,25.htm",
        "https://www.glassdoor.ca/Job/canada-qa-engineer-jobs-SRCH_IL.0,6_IN3_KO7,18.htm",
        "https://www.glassdoor.com/Job/united-states-qa-analyst-jobs-SRCH_IL.0,13_IN1_KO14,24.htm"
    ],
    "ZipRecruiter": [
        "https://www.ziprecruiter.com/jobs-search?search=QA+Engineer&location=United+States",
        "https://www.ziprecruiter.com/jobs-search?search=QA+Engineer&location=Canada",
        "https://www.ziprecruiter.com/jobs-search?search=QA+Analyst&location=United+States",
        "https://www.ziprecruiter.com/jobs-search?search=QA+Analyst&location=Canada"
    ],
    "Dice": [
        "https://www.dice.com/jobs?q=QA+&location=United+States&radiusUnit=mi&latitude=38.7945952&longitude=-106.5348379&countryCode=US&locationPrecision=Country",
        "https://www.dice.com/jobs?q=QA+&location=Canada&radiusUnit=mi&latitude=56.130366&longitude=-106.346771&countryCode=CA&locationPrecision=Country"
    ],
    "SimplyHired": [
        "https://www.simplyhired.com/search?q=QA+Engineer&l=United+States&s=d",
        "https://www.simplyhired.ca/search?q=QA+Engineer&l=Canada&s=d",
        "https://www.simplyhired.com/search?q=QA+Analyst&l=United+States&s=d",
        "https://www.simplyhired.ca/search?q=QA+Analyst&l=Canada&s=d"
    ]
}

# Only keep jobs posted within this many days. Jobs whose Posting_Date can't
# be parsed are dropped so the spreadsheet only contains clearly recent jobs.
MAX_JOB_AGE_DAYS = 3

# When True, jobs with missing/unreadable posting dates are kept so we can
# verify which job boards are scraping. Keep this False for normal runs.
KEEP_UNDATED_JOBS_FOR_REVIEW = False

# Software QA/testing job titles we want to keep. Some boards (notably
# SimplyHired) match loosely on individual words, which pulls in unrelated
# manufacturing/mechanical "Quality Engineer" roles. This is a content-level
# safety net applied after scraping, regardless of how good the search URL is.
RELEVANT_TITLE_KEYWORDS = [
    "qa engineer", "qa analyst", "quality assurance engineer",
    "quality assurance analyst", "test engineer", "sdet",
    "automation engineer", "software tester", "qa tester",
    "quality engineer (software)", "software quality"
]

# Title words that strongly indicate a NON-software role, even if "quality
# engineer" appears. Used to reject manufacturing/mechanical matches.
EXCLUDED_TITLE_KEYWORDS = [
    "mechanical", "manufacturing", "machinist", "welding", "supplier quality",
    "construction", "civil engineer", "electrical engineer", "hardware test",
    "process engineer", "plant", "production quality", "food safety",
    "pharmaceutical", "chemical engineer"
]

def is_relevant_title(title):
    """Keep titles that look like software QA roles, reject ones that look
    like manufacturing/mechanical Quality Engineer roles."""
    if not title:
        return False
    text = str(title).strip().lower()

    if any(bad in text for bad in EXCLUDED_TITLE_KEYWORDS):
        return False

    if any(good in text for good in RELEVANT_TITLE_KEYWORDS):
        return True

    # Fallback: "qa" as a standalone word is a decent signal even if it
    # doesn't match a known phrase above
    import re
    if re.search(r"\bqa\b", text):
        return True

    return False

def infer_country_from_url(url):
    """Infer the searched country from the job-board URL."""
    text = str(url).lower()
    if "canada" in text or ".ca/" in text or "l=canada" in text:
        return "Canada"
    if "united%20states" in text or "united+states" in text or "united-states" in text or "l=united" in text:
        return "United States"
    return "N/A"

def format_location(location, country):
    """Prefix the location with the searched country for easier Excel filtering."""
    location_text = str(location).strip() if location else ""
    country_text = str(country).strip() if country else ""

    if not location_text or location_text == "N/A":
        return country_text if country_text and country_text != "N/A" else "N/A"

    if not country_text or country_text == "N/A":
        return location_text

    if location_text.lower().startswith(f"{country_text.lower()} - "):
        return location_text

    return f"{country_text} - {location_text}"

POSTING_AGE_PATTERN = re.compile(
    r"(just posted|just now|today|yesterday|\d+\s*(?:minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w)\s*(?:ago)?)",
    re.IGNORECASE
)

def extract_posting_date_from_text(text):
    """Find a relative posting date inside a larger job-card text block."""
    if not text:
        return "N/A"
    cleaned_text = re.sub(r"\s+", " ", str(text)).strip()
    date_match = POSTING_AGE_PATTERN.search(cleaned_text)
    if not date_match:
        return "N/A"

    return normalize_posting_date(date_match.group(1))

def normalize_posting_date(posting_date):
    """Clean job-board posting dates into a consistent relative-date format."""
    if not posting_date:
        return "N/A"

    text = re.sub(r"\s+", " ", str(posting_date)).strip()
    text = re.sub(r"^(posted|posted\s+on)\s+", "", text, flags=re.IGNORECASE)

    if not text:
        return "N/A"

    lowered = text.lower()
    if lowered in {"today", "yesterday", "just posted", "just now"}:
        return lowered.title()

    relative_match = re.search(
        r"(\d+)\s*(minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w)\b(?:\s*ago)?",
        lowered
    )
    if not relative_match:
        return text

    amount = int(relative_match.group(1))
    unit = relative_match.group(2)

    if unit in {"m", "min", "mins", "minute", "minutes"}:
        label = "minute" if amount == 1 else "minutes"
    elif unit in {"h", "hr", "hrs", "hour", "hours"}:
        label = "hour" if amount == 1 else "hours"
    elif unit in {"d", "day", "days"}:
        label = "day" if amount == 1 else "days"
    else:
        label = "week" if amount == 1 else "weeks"

    return f"{amount} {label} ago"

def split_location_and_posting_date(location, posting_date="N/A"):
    """Split Dice-style 'City, State • Today' text into location and date."""
    location_text = re.sub(r"\s+", " ", str(location or "")).strip()
    posting_date_text = normalize_posting_date(posting_date)

    if location_text:
        location_date_match = re.match(
            r"^(?P<location>.+?)\s*\W+\s*(?P<date>just posted|just now|today|yesterday|\d+\s*(?:minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w)\s*(?:ago)?)\s*$",
            location_text,
            re.IGNORECASE
        )
        if location_date_match:
            date_from_right = extract_posting_date_from_text(location_date_match.group("date"))
            if date_from_right != "N/A":
                location_text = location_date_match.group("location").strip()
                if posting_date_text == "N/A":
                    posting_date_text = date_from_right

    return (location_text or "N/A", posting_date_text)

def parse_dice_card_text(title, card_text, company="N/A", location="N/A", posting_date="N/A"):
    """Fill Dice company/location/date from the visible card text."""
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in str(card_text or "").splitlines()
        if re.sub(r"\s+", " ", line).strip()
    ]

    title_text = re.sub(r"\s+", " ", str(title or "")).strip()
    company_text = str(company or "N/A").strip() or "N/A"
    if not is_dice_company_candidate(company_text, title_text):
        company_text = "N/A"
    location_text = str(location or "N/A").strip() or "N/A"
    posting_date_text = normalize_posting_date(posting_date)

    company_from_description = extract_dice_company_from_text(card_text)
    if company_from_description != "N/A":
        company_text = company_from_description

    title_index = None
    for index, line in enumerate(lines):
        if line.lower() == title_text.lower():
            title_index = index
            break

    if title_index is None:
        for index, line in enumerate(lines):
            if title_text and (title_text.lower() in line.lower() or line.lower() in title_text.lower()):
                title_index = index
                break

    if title_index is not None:
        if company_text == "N/A":
            candidate_indexes = list(range(title_index - 1, -1, -1)) + list(range(title_index + 1, min(len(lines), title_index + 5)))
            for candidate_index in candidate_indexes:
                line = lines[candidate_index]
                if is_dice_company_candidate(line, title_text):
                    company_text = line
                    break

        for line in lines[title_index + 1:title_index + 5]:
            possible_location, possible_date = split_location_and_posting_date(line, posting_date_text)
            if possible_date != "N/A":
                location_text = possible_location
                posting_date_text = possible_date
                break

    if posting_date_text == "N/A":
        posting_date_text = extract_posting_date_from_text(card_text)

    return company_text, location_text, posting_date_text

def is_dice_company_candidate(line, title_text=""):
    """Return True when a Dice card line looks like a company name."""
    text = re.sub(r"\s+", " ", str(line or "")).strip()
    lowered = text.lower()
    title_lowered = str(title_text or "").lower()

    if not text or len(text) <= 1:
        return False
    if len(text) > 60:
        return False
    if lowered == title_lowered:
        return False
    if extract_posting_date_from_text(text) != "N/A":
        return False
    if lowered in {"remote", "hybrid", "onsite", "on-site", "full-time", "contract"}:
        return False
    if lowered.startswith(("http://", "https://", "job title:", "summary:", "description:")):
        return False
    if lowered.startswith((
        "we ", "we're ", "we are ", "the ", "this ", "our ", "as ", "about ",
        "hello", "looking ", "job ", "role ", "responsibilities"
    )):
        return False
    if re.search(r"\b(is|are|was|were|will|seeking|hiring)\b", lowered) and len(text.split()) > 3:
        return False
    if any(skip in lowered for skip in (
        "easy apply", "apply now", "save", "saved", "full-time", "contract",
        "depends on experience", "third party", "posted", "remote or hybrid",
        "hybrid in ", "remote in ", "onsite", "job description"
    )):
        return False
    if re.search(r"\b(the|this|role|candidate|responsible|experience|testing|applications?|systems?|support|develop|execute|manual|automation|hiring|opportunity|seeking|quality|engineer|analyst)\b", lowered) and len(text.split()) > 4:
        return False
    if "," in text and re.search(r"\b(alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|new york|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|wisconsin|wyoming|ontario|quebec|british columbia|alberta|manitoba|saskatchewan)\b", lowered):
        return False

    return True

def extract_dice_company_from_text(card_text):
    """Extract company from Dice descriptions that include 'Company: ...'."""
    text = re.sub(r"\s+", " ", str(card_text or "")).strip()
    if not text:
        return "N/A"

    company_match = re.search(
        r"\bCompany:\s*(?P<company>.+?)(?:\s+About\b|\s+Role\b|\s+Key Responsibilities\b|\s+Responsibilities\b|\s+Job Description\b|$)",
        text,
        re.IGNORECASE
    )
    if not company_match:
        return "N/A"

    company = company_match.group("company").strip(" :-|<>")
    company = re.sub(r"\s+", " ", company)

    if is_dice_company_candidate(company):
        return company

    return "N/A"

# Initialize spreadsheet
SPREADSHEET_COLUMNS = [
    "Date_Found", "Title", "Company", "Location",
    "Link", "Source", "Posting_Date"
]

def init_spreadsheet():
    """Read the master job list from the All Jobs worksheet.

    Older workbook versions used a single unnamed/default worksheet, so this
    function falls back to the first worksheet to remain backward compatible.
    """
    try:
        workbook = pd.ExcelFile(SPREADSHEET_PATH)
        sheet_name = "All Jobs" if "All Jobs" in workbook.sheet_names else workbook.sheet_names[0]
        df = pd.read_excel(workbook, sheet_name=sheet_name)
    except FileNotFoundError:
        df = pd.DataFrame(columns=SPREADSHEET_COLUMNS)
        write_country_workbook(df)
    return df

def get_job_country(location):
    """Determine whether a saved location belongs to the US or Canada."""
    text = str(location or "").strip().lower()

    if text.startswith("canada -") or text == "canada":
        return "Canada"
    if text.startswith("united states -") or text == "united states":
        return "United States"

    return "Other / Unknown"

def write_country_workbook(df):
    """Write the master list plus separate US and Canada worksheets."""
    output_df = df.copy()

    if output_df.empty:
        us_df = output_df.copy()
        canada_df = output_df.copy()
        other_df = output_df.copy()
    else:
        country_series = output_df["Location"].apply(get_job_country)
        us_df = output_df[country_series == "United States"].copy()
        canada_df = output_df[country_series == "Canada"].copy()
        other_df = output_df[country_series == "Other / Unknown"].copy()

    with pd.ExcelWriter(SPREADSHEET_PATH, engine="openpyxl") as writer:
        output_df.to_excel(writer, sheet_name="All Jobs", index=False)
        us_df.to_excel(writer, sheet_name="United States", index=False)
        canada_df.to_excel(writer, sheet_name="Canada", index=False)

        # Preserve jobs whose location could not be confidently assigned, rather
        # than silently hiding them from the country-specific worksheets.
        if not other_df.empty:
            other_df.to_excel(writer, sheet_name="Other-Unknown", index=False)

    print(
        "Workbook sheets updated: "
        f"All Jobs={len(output_df)}, United States={len(us_df)}, "
        f"Canada={len(canada_df)}, Other/Unknown={len(other_df)}"
    )

# Process job board specific scraping
def process_job_board(soup, source, search_country="N/A"):
    """Process job listings from different job boards"""
    jobs = []

    if source == "LinkedIn":
        job_cards = soup.select("[data-testid='job-search-result']")
        if not job_cards:
            job_cards = soup.select(".jobs-search-results__list-item, .job-search-card")

        print(f"Found {len(job_cards)} job cards on {source}")

        for card in job_cards[:10]:
            try:
                title_elem = (card.select_one(".job-card-list__title a") or
                            card.select_one(".job-card-list__title") or
                            card.select_one("[data-testid='job-title']") or
                            card.select_one("h3 a") or
                            card.select_one(".base-search-card__title"))

                company_elem = (card.select_one(".job-card-container__company-name") or
                              card.select_one("[data-testid='job-search-card-subtitle']") or
                              card.select_one(".base-search-card__subtitle") or
                              card.select_one("h4 a"))

                location_elem = (card.select_one(".job-card-container__metadata-item") or
                               card.select_one("[data-testid='job-search-card-location']") or
                               card.select_one(".job-search-card__location"))

                date_elem = (card.select_one("time") or
                           card.select_one(".job-search-card__listdate") or
                           card.select_one("[data-testid='job-search-card-date']"))

                link_elem = (card.select_one(".job-card-list__title a") or
                           card.select_one("h3 a") or
                           card.select_one(".base-search-card__title a"))

                if title_elem and company_elem:
                    title_text = title_elem.get_text(strip=True)
                    company_text = company_elem.get_text(strip=True)
                    location_text = location_elem.get_text(strip=True) if location_elem else "N/A"

                    posting_date = "N/A"
                    if date_elem:
                        if date_elem.get("datetime"):
                            posting_date = date_elem["datetime"]
                        else:
                            posting_date = date_elem.get_text(strip=True)

                    link_url = ""
                    if link_elem and link_elem.get("href"):
                        link_url = link_elem["href"]
                        if link_url.startswith("/"):
                            link_url = "https://www.linkedin.com" + link_url

                    jobs.append({
                        "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title_text,
                        "Company": company_text,
                        "Location": format_location(location_text, search_country),
                        "Link": link_url,
                        "Source": source,
                        "Posting_Date": posting_date
                    })
                    print(f"Scraped: {title_text} at {company_text}")

            except Exception as e:
                print(f"Error processing job card: {e}")
                continue

    elif source == "Indeed":
        job_cards = soup.select("[data-jk]")
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

                    posting_date = "N/A"
                    if date_elem:
                        posting_date = date_elem.get_text(strip=True)
                    else:
                        import re
                        card_text = card.get_text(" ", strip=True)
                        date_match = re.search(
                            r"(just posted|just now|today|yesterday|\d+\s*(?:minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w)\s*(?:ago)?)",
                            card_text,
                            re.IGNORECASE
                        )
                        if date_match:
                            posting_date = date_match.group(1)
                    location_text, posting_date = split_location_and_posting_date(location_text, posting_date)

                    link_url = ""
                    if link_elem and link_elem.get("href"):
                        link_url = link_elem["href"]
                        if link_url.startswith("/"):
                            link_url = "https://www.indeed.com" + link_url

                    jobs.append({
                        "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title_text,
                        "Company": company_text,
                        "Location": format_location(location_text, search_country),
                        "Link": link_url,
                        "Source": source,
                        "Posting_Date": posting_date
                    })
                    print(f"Scraped: {title_text} at {company_text}")

            except Exception as e:
                print(f"Error processing Indeed job card: {e}")
                continue

    elif source == "Glassdoor":
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

                    posting_date = "N/A"
                    if date_elem:
                        posting_date = date_elem.get_text(strip=True)
                    else:
                        import re
                        card_text = card.get_text(" ", strip=True)
                        date_match = re.search(
                            r"(just posted|just now|today|yesterday|\d+\s*(?:minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w)\s*(?:ago)?)",
                            card_text,
                            re.IGNORECASE
                        )
                        if date_match:
                            posting_date = date_match.group(1)
                    location_text, posting_date = split_location_and_posting_date(location_text, posting_date)

                    link_url = ""
                    if link_elem and link_elem.get("href"):
                        link_url = link_elem["href"]
                        if link_url.startswith("/"):
                            link_url = "https://www.glassdoor.com" + link_url

                    jobs.append({
                        "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title_text,
                        "Company": company_text,
                        "Location": format_location(location_text, search_country),
                        "Link": link_url,
                        "Source": source,
                        "Posting_Date": posting_date
                    })
                    print(f"Scraped: {title_text} at {company_text}")

            except Exception as e:
                print(f"Error processing Glassdoor job card: {e}")
                continue

    elif source == "ZipRecruiter":
        job_cards = soup.select("[data-testid='job-card']")
        if not job_cards:
            job_cards = soup.select(".job_content, .jobList-item")

        print(f"Found {len(job_cards)} job cards on {source}")

        for card in job_cards[:10]:
            try:
                title_elem = (card.select_one("[data-testid='job-title']") or
                             card.select_one(".jobList-title") or
                             card.select_one("h2 a") or
                             card.select_one(".title"))

                company_elem = (card.select_one("[data-testid='company-name']") or
                               card.select_one(".jobList-company") or
                               card.select_one(".company_name"))

                location_elem = (card.select_one("[data-testid='job-location']") or
                                card.select_one(".jobList-location") or
                                card.select_one(".location"))

                date_elem = card.select_one(".jobList-date") or card.select_one("[data-testid='job-age']")

                link_elem = (card.select_one("a[data-testid='job-title-link']") or
                            card.select_one("h2 a") or
                            card.select_one(".title a"))

                if title_elem and company_elem:
                    title_text = title_elem.get_text(strip=True)
                    company_text = company_elem.get_text(strip=True)
                    location_text = location_elem.get_text(strip=True) if location_elem else "N/A"

                    posting_date = "N/A"
                    if date_elem:
                        posting_date = date_elem.get_text(strip=True)
                    else:
                        posting_date = datetime.now().strftime("%Y-%m-%d")

                    link_url = ""
                    if link_elem and link_elem.get("href"):
                        link_url = link_elem["href"]
                        if link_url.startswith("/"):
                            link_url = "https://www.ziprecruiter.com" + link_url

                    jobs.append({
                        "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title_text,
                        "Company": company_text,
                        "Location": format_location(location_text, search_country),
                        "Link": link_url,
                        "Source": source,
                        "Posting_Date": posting_date
                    })
                    print(f"Scraped: {title_text} at {company_text}")

            except Exception as e:
                print(f"Error processing ZipRecruiter job card: {e}")
                continue

    elif source == "Dice":
        # Dice loads job cards dynamically and its selectors can change.
        # Try the web-component selector first, then fall back to data-cy
        # cards, generic cards, and article tags.
        job_cards = soup.select("dhi-search-result")
        if not job_cards:
            job_cards = soup.select("[data-cy='card'], [data-testid='job-search-card'], .card, article, div:has(a[href*='/job-detail/'])")

        print(f"Found {len(job_cards)} job cards on {source}")

        for card in job_cards[:10]:
            try:
                title_elem = (card.select_one("[data-cy='card-title-link']") or
                             card.select_one(".card-title-link") or
                             card.select_one("a.title") or
                             card.select_one("h5 a") or
                             card.select_one("a[href*='/job-detail/']"))

                company_elem = (card.select_one("[data-cy='search-result-company-name']") or
                               card.select_one("[data-testid='company-name']") or
                               card.select_one(".company-name") or
                               card.select_one(".company") or
                               card.select_one(".employer-name"))

                location_elem = (card.select_one("[data-cy='search-result-location']") or
                                card.select_one("[data-testid='job-location']") or
                                card.select_one(".location") or
                                card.select_one(".search-result-location"))

                date_elem = (card.select_one("[data-cy='card-posted-date']") or
                            card.select_one("[data-testid='posted-date']") or
                            card.select_one(".posted-date"))

                link_elem = (card.select_one("[data-cy='card-title-link']") or
                            card.select_one("a.title") or
                            card.select_one("h5 a") or
                            card.select_one("a[href*='/job-detail/']"))

                if title_elem and company_elem:
                    title_text = title_elem.get_text(strip=True)
                    company_text = company_elem.get_text(strip=True)
                    location_text = location_elem.get_text(strip=True) if location_elem else "N/A"

                    posting_date = "N/A"
                    if date_elem:
                        posting_date = date_elem.get_text(strip=True)
                    else:
                        import re
                        card_text = card.get_text(" ", strip=True)
                        date_match = re.search(
                            r"(just posted|just now|today|yesterday|\d+\s*(?:minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w)\s*(?:ago)?)",
                            card_text,
                            re.IGNORECASE
                        )
                        if date_match:
                            posting_date = date_match.group(1)

                    link_url = ""
                    if link_elem and link_elem.get("href"):
                        link_url = link_elem["href"]
                        if link_url.startswith("/"):
                            link_url = "https://www.dice.com" + link_url

                    jobs.append({
                        "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title_text,
                        "Company": company_text,
                        "Location": format_location(location_text, search_country),
                        "Link": link_url,
                        "Source": source,
                        "Posting_Date": posting_date
                    })
                    print(f"Scraped: {title_text} at {company_text}")

            except Exception as e:
                print(f"Error processing Dice job card: {e}")
                continue

    elif source == "SimplyHired":
        job_cards = soup.select("[data-testid='searchSerpJob']")
        if not job_cards:
            job_cards = soup.select(".SerpJob, .jobposting-snippet")

        print(f"Found {len(job_cards)} job cards on {source}")

        for card in job_cards[:10]:
            try:
                title_elem = (card.select_one("[data-testid='searchSerpJobTitle']") or
                             card.select_one("h3 a") or
                             card.select_one(".title"))

                company_elem = (card.select_one("[data-testid='searchSerpJobCompanyName']") or
                               card.select_one(".company") or
                               card.select_one("[data-testid='companyName']"))

                location_elem = (card.select_one("[data-testid='searchSerpJobLocation']") or
                                card.select_one(".location") or
                                card.select_one("[data-testid='jobLocation']"))

                date_elem = (card.select_one("[data-testid='searchSerpJobAge']") or
                            card.select_one(".date"))

                link_elem = (card.select_one("h3 a") or
                            card.select_one(".title a") or
                            card.select_one("a[data-testid='searchSerpJobTitle']"))

                if title_elem and company_elem:
                    title_text = title_elem.get_text(strip=True)
                    company_text = company_elem.get_text(strip=True)
                    location_text = location_elem.get_text(strip=True) if location_elem else "N/A"

                    posting_date = "N/A"
                    if date_elem:
                        posting_date = date_elem.get_text(strip=True)
                    else:
                        posting_date = datetime.now().strftime("%Y-%m-%d")

                    link_url = ""
                    if link_elem and link_elem.get("href"):
                        link_url = link_elem["href"]
                        if link_url.startswith("/"):
                            link_url = "https://www.simplyhired.com" + link_url

                    jobs.append({
                        "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                        "Title": title_text,
                        "Company": company_text,
                        "Location": format_location(location_text, search_country),
                        "Link": link_url,
                        "Source": source,
                        "Posting_Date": posting_date
                    })
                    print(f"Scraped: {title_text} at {company_text}")

            except Exception as e:
                print(f"Error processing SimplyHired job card: {e}")
                continue

    return jobs

# Scrape job listings
def process_dice_from_browser(driver, search_country="N/A"):
    """Extract Dice results directly from the rendered browser page."""
    dice_cards = driver.execute_script("""
        const cardSelectors = [
            "dhi-search-result",
            "[data-cy='card']",
            "[data-testid='job-search-card']",
            "article"
        ];
        let cards = [];
        for (const selector of cardSelectors) {
            cards = Array.from(document.querySelectorAll(selector));
            if (cards.length) break;
        }

        if (!cards.length) {
            const links = Array.from(document.querySelectorAll("a[href*='/job-detail/'], a[href*='/jobs/detail/']"));
            const seen = new Set();
            cards = links
                .map(link => {
                    const explicitCard = link.closest("dhi-search-result, [data-cy='card'], [data-testid='job-search-card'], article, li, [class*='card'], [class*='Card']");
                    if (explicitCard) return explicitCard;

                    let node = link;
                    for (let i = 0; i < 6 && node && node.parentElement; i++) {
                        node = node.parentElement;
                        const text = (node.innerText || "").trim();
                        if (
                            /(?:today|yesterday|just posted|just now|\\d+\\s*(?:minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w)\\b)/i.test(text) &&
                            text.length > 40
                        ) {
                            return node;
                        }
                    }

                    return link.parentElement;
                })
                .filter(card => {
                    if (!card || seen.has(card)) return false;
                    seen.add(card);
                    return true;
                });
        }

        return cards.slice(0, 20).map(card => {
            const titleLink = card.querySelector(
                "[data-cy='card-title-link'], a[href*='/job-detail/'], a[href*='/jobs/detail/'], h5 a, a"
            );
            const companyEl = card.querySelector(
                "[data-cy='search-result-company-name'], [data-cy*='company'], [data-testid='company-name'], [data-testid*='company'], [aria-label*='company'], .company-name, .company, .employer-name, [class*='company'], [class*='Company']"
            );
            const locationEl = card.querySelector(
                "[data-cy='search-result-location'], [data-testid='job-location'], .location, .search-result-location"
            );
            const dateEl = card.querySelector(
                "[data-cy='card-posted-date'], [data-testid='posted-date'], [aria-label*='Posted'], [class*='posted'], [class*='Posted'], .posted-date"
            );
            const cardText = (card.innerText || "").trim();
            const linkLines = Array.from(card.querySelectorAll("a"))
                .map(link => ({
                    text: (link.innerText || link.textContent || "").trim(),
                    href: (link.href || "").trim(),
                    aria: (link.getAttribute("aria-label") || "").trim()
                }))
                .filter(link => link.text);
            const titleText = (titleLink && titleLink.innerText || "").trim();
            const titleHref = (titleLink && titleLink.href || "").trim();
            const companyFromLink = linkLines.find(link => {
                const text = link.text.toLowerCase();
                const href = link.href.toLowerCase();
                if (!text || link.text === titleText || link.href === titleHref) return false;
                if (href.includes("/job-detail/") || href.includes("/jobs/detail/")) return false;
                if (text.includes("apply") || text.includes("save") || text.includes("alert")) return false;
                return true;
            });
            const dateFromText = cardText.match(
                /(?:posted\\s+)?(just posted|just now|today|yesterday|\\d+\\s*(?:minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w)\\s*(?:ago)?)/i
            );
            return {
                title: titleText,
                company: (companyEl && companyEl.innerText || companyFromLink && companyFromLink.text || "").trim(),
                location: (locationEl && locationEl.innerText || "").trim(),
                postingDate: (dateEl && dateEl.innerText || dateFromText && dateFromText[1] || "").trim(),
                link: (titleLink && titleLink.href || "").trim(),
                text: [cardText].concat(linkLines.map(link => link.text)).join("\\n")
            };
        });
    """)

    jobs = []
    print(f"Dice browser fallback found {len(dice_cards)} rendered card(s)")

    for card in dice_cards:
        title_text = card.get("title") or ""
        link_url = card.get("link") or ""
        if not title_text or not link_url:
            continue

        company_text = card.get("company") or "N/A"
        location_text = card.get("location") or "N/A"
        posting_date = normalize_posting_date(card.get("postingDate")) if card.get("postingDate") else extract_posting_date_from_text(card.get("text"))
        company_text, location_text, posting_date = parse_dice_card_text(
            title_text,
            card.get("text"),
            company_text,
            location_text,
            posting_date
        )
        location_text, posting_date = split_location_and_posting_date(location_text, posting_date)

        jobs.append({
            "Date_Found": datetime.now().strftime("%Y-%m-%d"),
            "Title": title_text,
            "Company": company_text,
            "Location": format_location(location_text, search_country),
            "Link": link_url,
            "Source": "Dice",
            "Posting_Date": posting_date
        })
        print(f"Scraped from Dice browser fallback: {title_text} at {company_text} ({posting_date})")

    return jobs

def click_dice_filter_text(driver, text, timeout=8):
    """Click a Dice filter option by visible text, tolerating count suffixes."""
    xpath = (
        "//*[self::button or self::label or self::span or self::div]"
        f"[contains(translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
        f"'{text.lower()}')]"
    )

    end_time = time.time() + timeout
    while time.time() < end_time:
        elements = driver.find_elements(By.XPATH, xpath)
        for element in elements:
            try:
                if not element.is_displayed():
                    continue

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                continue
        time.sleep(0.5)

    return False

def apply_dice_filters(driver):
    """Use Dice's filter drawer to select Last 3 days plus Remote/Hybrid."""
    print("Applying Dice filters: Last 3 days, Remote, Hybrid")

    if not click_dice_filter_text(driver, "all filters"):
        print("Could not open Dice filters; continuing without UI filters.")
        return

    time.sleep(1)

    if not click_dice_filter_text(driver, "last 3 days"):
        print("Could not select Dice posted-date filter: Last 3 days")

    for work_setting in ("remote", "hybrid"):
        if not click_dice_filter_text(driver, work_setting):
            print(f"Could not select Dice work setting filter: {work_setting.title()}")

    if click_dice_filter_text(driver, "apply filters"):
        time.sleep(5)
    else:
        print("Could not click Dice Apply filters; continuing with current results.")

def close_ziprecruiter_modal(driver):
    """Close ZipRecruiter email/signup modal when it appears over results."""
    close_selectors = [
        "button[aria-label='Close']",
        "button[aria-label*='close' i]",
        "[data-testid='modal-close']",
        "[class*='close'] button",
    ]

    for selector in close_selectors:
        try:
            for element in driver.find_elements(By.CSS_SELECTOR, selector):
                if element.is_displayed():
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(1)
                    return True
        except Exception:
            continue

    try:
        driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")  # Escape
        time.sleep(1)
    except Exception:
        pass

    return False

def process_ziprecruiter_from_browser(driver, search_country="N/A"):
    """Extract ZipRecruiter jobs directly from the rendered browser page."""
    close_ziprecruiter_modal(driver)

    zip_cards = driver.execute_script("""
        const selectors = [
            "[data-testid='job-card']",
            "article",
            "[class*='job']",
            "li"
        ];
        let cards = [];
        for (const selector of selectors) {
            cards = Array.from(document.querySelectorAll(selector)).filter(card => {
                const text = (card.innerText || "").trim();
                return text.length > 40 && card.querySelector("a[href*='/jobs/'], a[href*='ziprecruiter.com']");
            });
            if (cards.length) break;
        }

        if (!cards.length) {
            const links = Array.from(document.querySelectorAll("a[href*='/jobs/']"));
            const seen = new Set();
            cards = links
                .map(link => link.closest("[data-testid='job-card'], article, li, [class*='job'], div") || link.parentElement)
                .filter(card => {
                    if (!card || seen.has(card)) return false;
                    seen.add(card);
                    return (card.innerText || "").trim().length > 40;
                });
        }

        return cards.slice(0, 20).map(card => {
            const titleLink = card.querySelector(
                "[data-testid='job-title'] a, a[data-testid='job-title-link'], h2 a, h3 a, a[href*='/jobs/']"
            );
            const companyEl = card.querySelector(
                "[data-testid='company-name'], [class*='company'], [class*='Company']"
            );
            const locationEl = card.querySelector(
                "[data-testid='job-location'], [class*='location'], [class*='Location']"
            );
            const dateEl = card.querySelector(
                "[data-testid='job-age'], [class*='date'], [class*='Date'], [class*='posted'], [class*='Posted']"
            );
            const cardText = (card.innerText || "").trim();
            return {
                title: (titleLink && titleLink.innerText || "").trim(),
                company: (companyEl && companyEl.innerText || "").trim(),
                location: (locationEl && locationEl.innerText || "").trim(),
                postingDate: (dateEl && dateEl.innerText || "").trim(),
                link: (titleLink && titleLink.href || "").trim(),
                text: cardText
            };
        });
    """)

    jobs = []
    print(f"ZipRecruiter browser fallback found {len(zip_cards)} rendered card(s)")

    for card in zip_cards:
        title_text = card.get("title") or ""
        link_url = card.get("link") or ""
        if not title_text or not link_url:
            continue

        company_text = card.get("company") or "N/A"
        location_text = card.get("location") or "N/A"
        posting_date = normalize_posting_date(card.get("postingDate")) if card.get("postingDate") else extract_posting_date_from_text(card.get("text"))

        jobs.append({
            "Date_Found": datetime.now().strftime("%Y-%m-%d"),
            "Title": title_text,
            "Company": company_text,
            "Location": format_location(location_text, search_country),
            "Link": link_url,
            "Source": "ZipRecruiter",
            "Posting_Date": posting_date
        })
        print(f"Scraped from ZipRecruiter browser fallback: {title_text} at {company_text} ({posting_date})")

    return jobs

def process_indeed_from_browser(driver, search_country="N/A"):
    """Extract Indeed jobs directly from the rendered browser page."""
    indeed_cards = driver.execute_script("""
        const selectors = [
            "[data-jk]",
            ".job_seen_beacon",
            "li:has(a[href*='/rc/clk'])",
            "li:has(a[href*='/pagead/clk'])",
            "div:has(a[href*='/rc/clk'])"
        ];
        let cards = [];
        for (const selector of selectors) {
            cards = Array.from(document.querySelectorAll(selector)).filter(card => {
                const text = (card.innerText || "").trim();
                return text.length > 40 && card.querySelector("a[href*='/rc/clk'], a[href*='/pagead/clk'], a[data-jk]");
            });
            if (cards.length) break;
        }

        return cards.slice(0, 20).map(card => {
            const titleLink = card.querySelector(
                "h2 a, a[data-jk], a[href*='/rc/clk'], a[href*='/pagead/clk']"
            );
            const titleEl = card.querySelector(
                "[data-testid='jobTitle'], .jobTitle span, h2 span, h2 a"
            );
            const companyEl = card.querySelector(
                "[data-testid='company-name'], .companyName, [class*='companyName'], [class*='Company']"
            );
            const locationEl = card.querySelector(
                "[data-testid='text-location'], [data-testid='job-location'], .companyLocation, [class*='location'], [class*='Location']"
            );
            const dateEl = card.querySelector(
                "[data-testid='myJobsStateDate'], [data-testid='job-age'], .date, [class*='date'], [class*='Date']"
            );
            const cardText = (card.innerText || "").trim();
            return {
                title: (titleEl && titleEl.innerText || titleLink && titleLink.innerText || "").trim(),
                company: (companyEl && companyEl.innerText || "").trim(),
                location: (locationEl && locationEl.innerText || "").trim(),
                postingDate: (dateEl && dateEl.innerText || "").trim(),
                link: (titleLink && titleLink.href || "").trim(),
                text: cardText
            };
        });
    """)

    jobs = []
    print(f"Indeed browser fallback found {len(indeed_cards)} rendered card(s)")

    for card in indeed_cards:
        title_text = card.get("title") or ""
        link_url = card.get("link") or ""
        if not title_text or not link_url:
            continue

        company_text = card.get("company") or "N/A"
        location_text = card.get("location") or "N/A"
        posting_date = normalize_posting_date(card.get("postingDate")) if card.get("postingDate") else extract_posting_date_from_text(card.get("text"))

        jobs.append({
            "Date_Found": datetime.now().strftime("%Y-%m-%d"),
            "Title": title_text,
            "Company": company_text,
            "Location": format_location(location_text, search_country),
            "Link": link_url,
            "Source": "Indeed",
            "Posting_Date": posting_date
        })
        print(f"Scraped from Indeed browser fallback: {title_text} at {company_text} ({posting_date})")

    return jobs

def get_source_ready_selector(source):
    selectors = {
        "LinkedIn": "[data-testid='job-search-result'], .jobs-search-results__list-item",
        "Indeed": "[data-jk], .job_seen_beacon",
        "Glassdoor": "[data-test='job-listing'], .react-job-listing",
        "ZipRecruiter": "[data-testid='job-card'], .jobList-item",
        "Dice": "dhi-search-result, [data-cy='card'], a[data-cy='card-title-link']",
        "SimplyHired": "[data-testid='searchSerpJob'], .SerpJob",
    }
    return selectors.get(source)

def page_looks_blocked(driver):
    text = f"{driver.title}\n{driver.page_source[:5000]}".lower()
    blocked_terms = [
        "captcha", "verify you are human", "verify it's you", "verify you",
        "unusual traffic", "security check", "are you a human",
        "access denied", "blocked", "robot", "humans only", "cloudflare",
        "just a moment"
    ]
    return any(term in text for term in blocked_terms)

def wait_for_manual_verification(driver, source, ready_selector):
    if source not in MANUAL_VERIFICATION_JOB_BOARDS:
        return False

    if not ready_selector:
        return False

    if not page_looks_blocked(driver):
        return False

    print(
        f"{source} appears to be asking for verification. "
        f"Please complete it in the Chrome window. Waiting up to "
        f"{MANUAL_VERIFICATION_TIMEOUT_SECONDS} seconds..."
    )

    end_time = time.time() + MANUAL_VERIFICATION_TIMEOUT_SECONDS
    while time.time() < end_time:
        try:
            if driver.find_elements(By.CSS_SELECTOR, ready_selector):
                print(f"{source} verification cleared; continuing scrape.")
                return True
        except Exception:
            pass
        time.sleep(5)

    print(f"{source} verification was not cleared in time; continuing with available page content.")
    return False

def recover_indeed_auth_redirect(driver, original_url):
    current_url = driver.current_url.lower()
    page_text = driver.page_source.lower()

    if "secure.indeed.com/auth" not in current_url and "invalid cors request" not in page_text:
        return False

    print("Indeed redirected to an auth/CORS page; returning to the search results URL.")
    driver.get(original_url)
    time.sleep(5)
    return True

def build_chrome_options(profile_path):
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return options

def create_chrome_driver():
    service = Service(ChromeDriverManager().install())

    try:
        driver = webdriver.Chrome(service=service, options=build_chrome_options(CHROME_PROFILE_PATH))
    except Exception as e:
        fallback_profile = os.path.abspath(
            os.path.join("chrome_profile_runtime", datetime.now().strftime("%Y%m%d_%H%M%S"))
        )
        print(f"Chrome could not start with the saved profile: {e}")
        print(f"Retrying with a fresh runtime Chrome profile: {fallback_profile}")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=build_chrome_options(fallback_profile))

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scrape_jobs():
    driver = create_chrome_driver()

    jobs = []

    try:
        # JOB_BOARDS maps each source to a LIST of URLs (one per country/region)
        for source, urls in JOB_BOARDS.items():
            if source in DISABLED_JOB_BOARDS:
                print(f"Skipping {source}: disabled because the site blocks automated scraping.")
                continue

            for url in urls:
                print(f"Scraping {source} ({url})...")
                driver.get(url)
                time.sleep(5)
                ready_selector = get_source_ready_selector(source)
                wait_for_manual_verification(driver, source, ready_selector)
                if source == "Indeed":
                    recover_indeed_auth_redirect(driver, url)

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
                    elif source == "ZipRecruiter":
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-card'], .jobList-item"))
                        )
                        close_ziprecruiter_modal(driver)
                    elif source == "Dice":
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "dhi-search-result, [data-cy='card'], a[data-cy='card-title-link']")
                            )
                        )
                        time.sleep(3)
                        apply_dice_filters(driver)
                    elif source == "SimplyHired":
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='searchSerpJob'], .SerpJob"))
                        )
                except Exception as e:
                    print(f"Failed to load job listings from {source} ({url}): {e}")
                    verification_cleared = wait_for_manual_verification(driver, source, ready_selector)
                    if source == "Indeed":
                        recover_indeed_auth_redirect(driver, url)
                    if source == "Dice" and verification_cleared:
                        apply_dice_filters(driver)
                    print("Continuing with available page content...")

                soup = BeautifulSoup(driver.page_source, "html.parser")
                search_country = infer_country_from_url(url)
                jobs_found = process_job_board(soup, source, search_country)
                if source == "Indeed" and len(jobs_found) == 0:
                    jobs_found = process_indeed_from_browser(driver, search_country)
                if source == "ZipRecruiter" and len(jobs_found) == 0:
                    jobs_found = process_ziprecruiter_from_browser(driver, search_country)
                if source == "Dice" and len(jobs_found) == 0:
                    jobs_found = process_dice_from_browser(driver, search_country)
                if len(jobs_found) == 0:
                    print(f"⚠ WARNING: 0 jobs found on {source} for this URL. "
                          f"This usually means the site served a CAPTCHA/block page "
                          f"instead of real results, or its page structure changed.")
                jobs.extend(jobs_found)

    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        driver.quit()

    print(f"Total jobs scraped: {len(jobs)}")
    return jobs

# Save jobs to spreadsheet
def is_within_age_limit(posting_date_str, max_days=MAX_JOB_AGE_DAYS):
    """
    Returns True if posting_date_str is within max_days of today.
    Handles two common formats:
      - ISO dates like '2026-06-17'
      - Relative strings like '3 days ago', '1 day ago', 'Today', 'Just posted'
    If the date can't be parsed at all, KEEP_UNDATED_JOBS_FOR_REVIEW controls
    whether the job is kept for troubleshooting.
    """
    if not posting_date_str or posting_date_str == "N/A":
        return KEEP_UNDATED_JOBS_FOR_REVIEW

    text = str(posting_date_str).strip().lower()

    # Relative formats: "today", "just posted", "1 day ago", "3d ago", "5h ago"
    if "today" in text or "just posted" in text or "just now" in text:
        return True
    if "yesterday" in text:
        return max_days >= 1

    import re
    relative_match = re.search(r"(\d+)\s*(day|days|d)\b", text)
    if relative_match:
        days_ago = int(relative_match.group(1))
        return days_ago <= max_days

    relative_hour_match = re.search(r"(\d+)\s*(hour|hours|hr|hrs|h)\b", text)
    if relative_hour_match:
        return True  # anything in hours is well within the window

    relative_minute_match = re.search(r"(\d+)\s*(minute|minutes|min|mins|m)\b", text)
    if relative_minute_match:
        return True

    relative_week_match = re.search(r"(\d+)\s*(week|weeks|wk|wks|w)\b", text)
    if relative_week_match:
        weeks_ago = int(relative_week_match.group(1))
        return weeks_ago * 7 <= max_days

    # Try parsing as an ISO/standard date (e.g. "2026-06-17")
    try:
        posting_date = pd.to_datetime(posting_date_str, errors="raise")
        age_days = (datetime.now() - posting_date).days
        return age_days <= max_days
    except (ValueError, TypeError):
        # Couldn't parse - optionally keep it while troubleshooting board coverage
        return KEEP_UNDATED_JOBS_FOR_REVIEW

def row_is_within_age_limit(row):
    posting_date = row.get("Posting_Date", "N/A")
    if is_within_age_limit(posting_date):
        return True

    if str(row.get("Source", "")).lower() == "simplyhired":
        return is_within_age_limit(row.get("Date_Found", "N/A"))

    return False

def print_source_counts(label, df):
    if df.empty or "Source" not in df.columns:
        print(f"{label}: 0 jobs")
        return

    counts = df["Source"].fillna("Unknown").value_counts().to_dict()
    formatted_counts = ", ".join(f"{source}: {count}" for source, count in counts.items())
    print(f"{label}: {formatted_counts}")

def clean_company_name_for_row(row):
    company = row.get("Company", "N/A")
    source = row.get("Source", "")
    title = row.get("Title", "")

    if str(source).lower() == "dice" and not is_dice_company_candidate(company, title):
        return "N/A"

    return company

def normalize_text(value):
    """Normalize text so small capitalization, spacing, and punctuation changes do not create duplicates."""
    if pd.isna(value):
        return ""

    text = str(value).strip().lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_company(value):
    """Normalize company names and remove common legal suffixes."""
    company = normalize_text(value)

    suffix_patterns = [
        r"\bincorporated\b",
        r"\bcorporation\b",
        r"\blimited\b",
        r"\binc\b",
        r"\bcorp\b",
        r"\bllc\b",
        r"\bltd\b",
        r"\bco\b",
    ]

    for suffix_pattern in suffix_patterns:
        company = re.sub(suffix_pattern, "", company)

    return re.sub(r"\s+", " ", company).strip()


def normalize_location(value):
    """Normalize location text while preserving meaningful city/state/country differences."""
    location = normalize_text(value)

    # Treat common remote wording consistently.
    location = re.sub(r"\bwork from home\b", "remote", location)
    location = re.sub(r"\bfully remote\b", "remote", location)
    location = re.sub(r"\bremote only\b", "remote", location)

    return re.sub(r"\s+", " ", location).strip()


def normalize_url(value):
    """Remove URL tracking parameters, fragments, and trailing slashes."""
    if pd.isna(value) or not str(value).strip():
        return ""

    url = str(value).strip()

    try:
        parts = urlsplit(url)
        normalized_path = parts.path.rstrip("/")
        return urlunsplit((
            parts.scheme.lower(),
            parts.netloc.lower(),
            normalized_path,
            "",
            "",
        ))
    except ValueError:
        return url.lower().rstrip("/")


def add_duplicate_keys(dataframe):
    """Return a copy with internal normalized fields used for duplicate detection."""
    keyed_df = dataframe.copy()

    for column in ["Title", "Company", "Location", "Link"]:
        if column not in keyed_df.columns:
            keyed_df[column] = ""

    keyed_df["_title_key"] = keyed_df["Title"].apply(normalize_text)
    keyed_df["_company_key"] = keyed_df["Company"].apply(normalize_company)
    keyed_df["_location_key"] = keyed_df["Location"].apply(normalize_location)
    keyed_df["_url_key"] = keyed_df["Link"].apply(normalize_url)
    return keyed_df


def remove_internal_duplicate_columns(dataframe):
    """Remove helper columns before returning or saving rows."""
    internal_columns = ["_title_key", "_company_key", "_location_key", "_url_key"]
    return dataframe.drop(
        columns=[column for column in internal_columns if column in dataframe.columns],
        errors="ignore",
    )


def save_to_spreadsheet(jobs):
    df = init_spreadsheet()
    new_jobs_df = pd.DataFrame(jobs)

    if not new_jobs_df.empty:
        new_jobs_df["Company"] = new_jobs_df.apply(clean_company_name_for_row, axis=1)
        print_source_counts("Scraped jobs by source before filters", new_jobs_df)

        # Drop jobs whose title does not look like a software QA role.
        relevant_mask = new_jobs_df["Title"].apply(is_relevant_title)
        irrelevant_count = int((~relevant_mask).sum())
        if irrelevant_count > 0:
            print(
                f"Filtered out {irrelevant_count} job(s) with non-QA titles "
                "(for example, manufacturing Quality Engineer roles)"
            )
        new_jobs_df = new_jobs_df[relevant_mask].copy()
        print_source_counts("Jobs by source after title filter", new_jobs_df)

        # Keep only recent postings.
        recent_mask = new_jobs_df.apply(row_is_within_age_limit, axis=1)
        stale_count = int((~recent_mask).sum())
        if stale_count > 0:
            print(
                f"Filtered out {stale_count} job(s) posted more than "
                f"{MAX_JOB_AGE_DAYS} days ago or with unclear dates"
            )
        new_jobs_df = new_jobs_df[recent_mask].copy()
        print_source_counts("Jobs by source after date filter", new_jobs_df)

        # Normalize incoming rows before comparing them.
        new_jobs_df = add_duplicate_keys(new_jobs_df)

        # Remove duplicates collected during this same scraping run. This is
        # important because one posting can appear under QA Engineer and QA Analyst
        # searches or under multiple country/location URLs.
        before_run_dedup = len(new_jobs_df)
        new_jobs_df = new_jobs_df.drop_duplicates(
            subset=["_title_key", "_company_key", "_location_key"],
            keep="first",
        ).copy()
        run_duplicate_count = before_run_dedup - len(new_jobs_df)
        if run_duplicate_count > 0:
            print(
                f"Removed {run_duplicate_count} duplicate job(s) found more than "
                "once during the current scraping run"
            )

        # Compare against normalized rows already stored in Excel.
        keyed_existing_df = add_duplicate_keys(df)
        existing_job_keys = set(zip(
            keyed_existing_df["_title_key"],
            keyed_existing_df["_company_key"],
            keyed_existing_df["_location_key"],
        ))
        existing_url_keys = {
            url_key for url_key in keyed_existing_df["_url_key"] if url_key
        }

        def is_genuinely_new(row):
            job_key = (
                row["_title_key"],
                row["_company_key"],
                row["_location_key"],
            )
            url_key = row["_url_key"]

            # A matching title/company/location is considered the same posting,
            # even when a job board changes tracking parameters in the link.
            if job_key in existing_job_keys:
                return False

            # Also reject a normalized URL that was already stored.
            if url_key and url_key in existing_url_keys:
                return False

            return True

        new_mask = new_jobs_df.apply(is_genuinely_new, axis=1)
        truly_new = new_jobs_df[new_mask].copy()
        duplicate_count = len(new_jobs_df) - len(truly_new)

        if duplicate_count > 0:
            print(f"Skipped {duplicate_count} job(s) already stored in the spreadsheet")

        print_source_counts("New jobs by source after duplicate check", truly_new)

        # Remove internal fields before combining with the spreadsheet.
        truly_new = remove_internal_duplicate_columns(truly_new)
        df = pd.concat([df, truly_new], ignore_index=True)
    else:
        truly_new = new_jobs_df

    # Re-apply filters to the whole spreadsheet so stale and off-topic rows are
    # cleaned out each time the script runs.
    before_filter_count = len(df)
    if not df.empty and {"Company", "Source", "Title"}.issubset(df.columns):
        df["Company"] = df.apply(clean_company_name_for_row, axis=1)

    if not df.empty:
        df = df[df.apply(row_is_within_age_limit, axis=1)].copy()
        df = df[df["Title"].apply(is_relevant_title)].copy()

    removed_count = before_filter_count - len(df)
    if removed_count > 0:
        print(f"Removed {removed_count} job(s) in the spreadsheet that were stale or off-topic")

    # Clean duplicates that may already exist from older script runs.
    if not df.empty:
        keyed_df = add_duplicate_keys(df)
        before_existing_dedup = len(keyed_df)

        # First remove exact normalized URL duplicates where a usable URL exists.
        with_url = keyed_df[keyed_df["_url_key"] != ""].drop_duplicates(
            subset=["_url_key"],
            keep="first",
        )
        without_url = keyed_df[keyed_df["_url_key"] == ""]
        keyed_df = pd.concat([with_url, without_url], ignore_index=True)

        # Then remove remaining title/company/location duplicates.
        keyed_df = keyed_df.drop_duplicates(
            subset=["_title_key", "_company_key", "_location_key"],
            keep="first",
        ).copy()

        existing_duplicates_removed = before_existing_dedup - len(keyed_df)
        if existing_duplicates_removed > 0:
            print(
                f"Removed {existing_duplicates_removed} duplicate job(s) already "
                "present in the spreadsheet"
            )

        df = remove_internal_duplicate_columns(keyed_df)

    write_country_workbook(df)

    # Return only user-facing columns for the email function.
    truly_new = remove_internal_duplicate_columns(truly_new)
    print(f"Saved {len(truly_new)} genuinely new job(s)")
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

if __name__ == "__main__":
    print("QA Engineer Job Tracker started...")
    print("This script will scrape job boards and create a comprehensive spreadsheet with job details.")

    # Schedule daily task
    schedule.every().day.at("09:00").do(process_jobs)

    process_jobs()  # Run immediately
    while True:
        schedule.run_pending()
        time.sleep(60)