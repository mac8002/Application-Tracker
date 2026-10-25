import time
import schedule
import smtplib
import pandas as pd
from datetime import datetime, date
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
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
from qa_classifier_candidate_v6 import classify_qa_job
from qa_description_extractor import extract_role_evidence
from qa_card_extractor_candidate_v2 import extract_card_role_evidence

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
    # Software QA and testing
    "qa engineer", "qa analyst", "quality assurance engineer",
    "quality assurance analyst", "test engineer", "sdet",
    "automation engineer", "software tester", "qa tester",
    "quality engineer (software)", "software quality",
    "manual tester", "manual test analyst",
    "software test analyst", "software test engineer",
    "test analyst", "software testing",
    "quality assurance tester", "functional tester",
    "regression tester",

    # Epic and healthcare IT
    "epic analyst", "epic application analyst",
    "epic systems analyst", "epic support analyst",
    "epic ambulatory analyst", "epic inpatient orders",
    "emr analyst", "ehr analyst",
    "clinical application analyst", "clinical systems analyst",
    "healthcare application analyst",
    "application analyst", "application systems analyst",
    "application support analyst"
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
    """Accept software QA and relevant healthcare IT job titles."""
    import re

    if not title:
        return False

    text = str(title).strip().lower()

    # Reject unrelated manufacturing/mechanical positions.
    if any(bad in text for bad in EXCLUDED_TITLE_KEYWORDS):
        return False

    # Recognize Epic healthcare IT titles regardless of word order.
    # Example: Associate IT Analyst (Epic)
    if re.search(r"\bepic\b", text) and any(
        term in text
        for term in ("analyst", "application", "systems", "support")
    ):
        return True

    # Existing QA titles and additional healthcare IT titles.
    if any(good in text for good in RELEVANT_TITLE_KEYWORDS):
        return True

    # Accept QA as a standalone word.
    if re.search(r"\bqa\b", text):
        return True

    # Allow generic Quality Engineer titles for description review.
    # Explicit manufacturing-related exclusions above still apply.
    if re.fullmatch(
        r"(?:(?:senior|sr\.?|junior|jr\.?|lead|principal|staff|"
        r"associate|entry.level|ii|iii|iv)\s+)*"
        r"quality engineer(?:\s+(?:i|ii|iii|iv|1|2|3|4))?",
        text
    ):
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

def parse_dice_card_text(title, card_text, company='N/A', location='N/A', posting_date='N/A'):
    """Fill Dice company/location/date from the visible card text."""
    lines = [re.sub('\\s+', ' ', line).strip() for line in str(card_text or '').splitlines() if re.sub('\\s+', ' ', line).strip()]
    title_text = re.sub('\\s+', ' ', str(title or '')).strip()
    company_text = str(company or 'N/A').strip() or 'N/A'
    if not is_dice_company_candidate(company_text, title_text):
        company_text = 'N/A'
    location_text = str(location or 'N/A').strip() or 'N/A'
    posting_date_text = normalize_posting_date(posting_date)
    company_from_description = extract_dice_company_from_text(card_text)
    if company_from_description != 'N/A':
        company_text = company_from_description
    title_index = None
    for (index, line) in enumerate(lines):
        if line.lower() == title_text.lower():
            title_index = index
            break
    if title_index is None:
        for (index, line) in enumerate(lines):
            if title_text and (title_text.lower() in line.lower() or line.lower() in title_text.lower()):
                title_index = index
                break
    if title_index is not None:
        if company_text == 'N/A':
            candidate_indexes = list(range(title_index - 1, -1, -1)) + list(range(title_index + 1, min(len(lines), title_index + 5)))
            for candidate_index in candidate_indexes:
                line = lines[candidate_index]
                if is_dice_company_candidate(line, title_text):
                    company_text = line
                    break
        for line in lines[title_index + 1:title_index + 5]:
            candidate_line = re.sub('\\s+', ' ', line).strip()
            location_like = bool(re.match('^(?:Remote|Hybrid|Onsite|On-site)(?:\\b|\\s+or\\b)', candidate_line, re.IGNORECASE) or re.search('\\b(?:in|at)\\s+[A-Za-z][^?|]*', candidate_line, re.IGNORECASE))
            if not location_like:
                continue
            (possible_location, possible_date) = split_location_and_posting_date(candidate_line, 'N/A')
            if possible_location != 'N/A':
                location_text = possible_location
            if possible_date != 'N/A':
                posting_date_text = possible_date
            break
    if posting_date_text == 'N/A':
        posting_date_text = extract_posting_date_from_text(card_text)
    return (company_text, location_text, posting_date_text)

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
    "Date_Found", "Last_Seen", "Title", "Company", "Location",
    "Link", "Source", "Posting_Date", "Posting_Date_Verified",
    "Application_Status", "Verification_Issue",
    "QA_Category", "Classification_Evidence",
    "Software_Score", "Manufacturing_Score",
    "Description"
]

def init_spreadsheet():
    """Read the master job list from the All Jobs worksheet.

    Older workbook versions used a single unnamed/default worksheet, so this
    function falls back to the first worksheet to remain backward compatible.
    """
    try:
        with pd.ExcelFile(SPREADSHEET_PATH) as workbook:
            sheet_name = next(
                (
                    name
                    for name in ("All Jobs - History", "All Jobs")
                    if name in workbook.sheet_names
                ),
                workbook.sheet_names[0]
            )
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
def deduplicate_view(df):
    """Deduplicate display views without deleting records from historical data."""
    if df.empty:
        return df.copy()

    copy = df.copy()
    copy["_view_key"] = copy.apply(
        lambda row: (
            normalize_text(row.get("Title")),
            normalize_company(row.get("Company"))
        ),
        axis=1
    )

    # Prefer entries with a valid link and a specific location.
    copy["_quality"] = copy.apply(
        lambda row: (
            int(valid_job_link(row.get("Link"))) * 2
            + int(
                str(row.get("Location", "")).strip().lower()
                not in {"", "n/a", "united states", "canada"}
            )
        ),
        axis=1
    )

    copy = (
        copy.sort_values("_quality", ascending=False)
        .drop_duplicates("_view_key", keep="first")
    )

    return copy.drop(columns=["_view_key", "_quality"])

def remote_eligibility(row):
    """Conservative text-only eligibility signal, not a verified employer policy."""
    title = str(row.get("Title", "")).lower()
    location = str(row.get("Location", "")).lower()
    combined = title + " " + location

    if "remote" not in combined and "work from home" not in combined:
        return "Not marked remote"

    if re.search(
        r"\b(latam|latin america|emea|apac|europe only|canada only)\b",
        combined
    ):
        return "Eligibility uncertain / non-US region"

    if get_job_country(row.get("Location")) != "United States":
        return "US eligibility unverified"

    return "US search result - verify eligibility"

def valid_job_link(value):
    """Return whether a value is an HTTP(S) job URL with a non-root path."""
    try:
        parts = urlsplit(str(value).strip())
        return (
            parts.scheme in {"http", "https"}
            and bool(parts.netloc)
            and parts.path not in {"", "/"}
        )
    except ValueError:
        return False

def write_country_workbook(df):
    """Preserve full history, and show deduplicated, clearly labeled review views."""
    output = df.copy()
    for column in SPREADSHEET_COLUMNS:
        if column not in output.columns:
            output[column] = ""
    output = output[SPREADSHEET_COLUMNS + [c for c in output.columns if c not in SPREADSHEET_COLUMNS]]
    if not output.empty:
        output = output.sort_values(["Date_Found", "Last_Seen"], ascending=False, na_position="last")
    today = pd.Timestamp(datetime.now().date())
    cutoff = today - pd.Timedelta(days=MAX_JOB_AGE_DAYS)
    def discovered_recent(row):
        date_found = pd.to_datetime(row.get("Date_Found"), errors="coerce")
        return pd.notna(date_found) and cutoff <= date_found.normalize() <= today
    recent = output[output.apply(lambda row: is_relevant_title(row.get("Title")) and
        row_is_within_age_limit(row) and not row_verification_issues(row), axis=1)].copy()
    discovered = output[output.apply(lambda row: discovered_recent(row) and
        is_relevant_title(row.get("Title")) and valid_job_link(row.get("Link")), axis=1)].copy()
    review = output[output.apply(lambda row: discovered_recent(row) and
        is_relevant_title(row.get("Title")) and (
            bool(row_verification_issues(row))
            or str(row.get("QA_Category", "")).strip().casefold()
            == "needs verification"
        ), axis=1)].copy()
    us = output[output["Location"].apply(get_job_country) == "United States"].copy()
    ca = output[output["Location"].apply(get_job_country) == "Canada"].copy()
    remote_candidates = discovered[discovered.apply(lambda row:
        "remote" in (str(row.get("Location", "")) + " " + str(row.get("Title", ""))).lower(), axis=1)].copy()
    if not remote_candidates.empty:
        remote_candidates["Remote_Eligibility"] = remote_candidates.apply(remote_eligibility, axis=1)
    us_remote = remote_candidates[remote_candidates["Remote_Eligibility"] == "US search result - verify eligibility"].copy() if not remote_candidates.empty else remote_candidates.copy()
    remote_uncertain = remote_candidates[remote_candidates["Remote_Eligibility"] != "US search result - verify eligibility"].copy() if not remote_candidates.empty else remote_candidates.copy()
    us_hybrid = discovered[discovered.apply(lambda row:
        get_job_country(row.get("Location")) == "United States" and
        "hybrid" in (str(row.get("Location", "")) + " " + str(row.get("Title", ""))).lower(), axis=1)].copy()
    views = [
        ("New - Last 3 Days", recent), ("Newly Discovered", discovered),
        ("US Remote - Review", us_remote), ("Remote Eligibility Check", remote_uncertain),
        ("US Hybrid", us_hybrid), ("Needs Verification", review),
        ("All Jobs - History", output), ("United States", us), ("Canada", ca),
    ]

    # Conservative QA classification filtering.
    # History and country worksheets retain all records.
    recommendation_names = {
        "New - Last 3 Days",
        "Newly Discovered",
        "US Remote - Review",
        "Remote Eligibility Check",
        "US Hybrid",
        "Needs Verification",
    }

    filtered_views = []

    for name, sheet in views:
        sheet = sheet.copy()

        if "QA_Category" not in sheet.columns:
            sheet["QA_Category"] = ""

        categories = (
            sheet["QA_Category"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        sheet["QA_Category"] = categories

        if name in recommendation_names:
            categories_lower = sheet["QA_Category"].str.casefold()
            manufacturing = categories_lower.eq("manufacturing qa")
            uncertain = categories_lower.eq("needs verification")

            if name == "Needs Verification":
                sheet = sheet.loc[~manufacturing].copy()
            else:
                sheet = sheet.loc[categories_lower.eq("software qa")].copy()

        filtered_views.append((name, sheet))

    views = filtered_views
    with pd.ExcelWriter(SPREADSHEET_PATH, engine="openpyxl") as writer:
        for name, sheet in views:
            if name != "All Jobs - History":
                sheet = deduplicate_view(sheet)
            sheet.to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            from openpyxl.styles import Font, PatternFill, Alignment
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="17365D")
                cell.alignment = Alignment(wrap_text=True)
            for col, width in {"A": 16, "B": 16, "C": 42, "D": 30, "E": 34, "F": 52,
                               "G": 18, "H": 18, "I": 24, "J": 22, "K": 44, "L": 34}.items():
                ws.column_dimensions[col].width = width
    print("Workbook updated: " + ", ".join(f"{name}={len(deduplicate_view(sheet)) if name != 'All Jobs - History' else len(sheet)}" for name, sheet in views))

# Process job board specific scraping

def safe_extract_card_role_evidence(card):
    """Preserve job records if description extraction fails."""
    try:
        result = extract_card_role_evidence(card)
        return result if isinstance(result, str) else ""
    except Exception:
        return ""


def process_job_board(soup, source, search_country="N/A", search_url=None):
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
                           card.select_one(".base-search-card__title a[href]") or
                            card.select_one('a[href*="/jobs/view/"]'))

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
                        "Posting_Date": posting_date,
                        "Description": safe_extract_card_role_evidence(card),
                    })
                    print(f"Scraped: {title_text} at {company_text}")

            except Exception as e:
                print(f"Error processing job card: {e}")
                continue

    elif source == "Indeed":
        job_cards = soup.select(".job_seen_beacon")
        if not job_cards:
            job_cards = soup.select(".job_seen_beacon")

        print(f"Found {len(job_cards)} job cards on {source}")

        for card in job_cards[:10]:
            try:
                title_elem = card.select_one("h2 a span") or card.select_one(".jobTitle a")
                company_elem = card.select_one(".companyName") or card.select_one("[data-testid='company-name']")
                location_elem = card.select_one("[data-testid='text-location']") or card.select_one("[data-testid='job-location']") or card.select_one(".companyLocation")
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
                        "Posting_Date": posting_date,
                        "Description": safe_extract_card_role_evidence(card),
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
                        "Posting_Date": posting_date,
                        "Description": safe_extract_card_role_evidence(card),
                    })
                    print(f"Scraped: {title_text} at {company_text}")

            except Exception as e:
                print(f"Error processing Glassdoor job card: {e}")
                continue

    elif source == "ZipRecruiter":
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        import re

        job_cards = soup.select("article[data-testid^='job-card-']")
        print(f"Found {len(job_cards)} job cards on {source}")

        for card in job_cards[:10]:
            try:
                title_elem = card.select_one(
                    "[data-testid='serp-job-card-title']"
                )
                company_elem = card.select_one("a[href*='/co/']")
                location_elem = card.select_one("a[href*='location=']")

                if not (title_elem and company_elem):
                    continue

                title_text = title_elem.get_text(" ", strip=True)
                company_text = company_elem.get_text(" ", strip=True)
                location_text = (
                    location_elem.get_text(" ", strip=True)
                    if location_elem else "N/A"
                )

                card_id = card.get("data-testid", "")
                job_id = card_id.removeprefix("job-card-")

                link_url = ""
                if card_id.startswith("job-card-") and job_id:
                    base_url = search_url or (
                        "https://www.ziprecruiter.com/jobs-search"
                        "?search=QA+Engineer&location=United+States"
                    )
                    parsed = urlparse(base_url)
                    params = parse_qs(parsed.query)
                    params["lk"] = [job_id]
                    link_url = urlunparse(
                        parsed._replace(
                            query=urlencode(params, doseq=True)
                        )
                    )

                posting_date = "N/A"
                badge = card.select_one(
                    "[data-testid='new-label-badge']"
                )

                if badge:
                    badge_text = badge.get_text(" ", strip=True)
                    if re.search(
                        r"posted|new|today|yesterday",
                        badge_text, re.IGNORECASE
                    ):
                        posting_date = badge_text

                jobs.append({
                    "Date_Found": datetime.now().strftime("%Y-%m-%d"),
                    "Title": title_text,
                    "Company": company_text,
                    "Location": format_location(
                        location_text, search_country
                    ),
                    "Link": link_url,
                    "Source": source,
                    "Posting_Date": posting_date,
                    "Description": safe_extract_card_role_evidence(card),
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
                        "Posting_Date": posting_date,
                        "Description": safe_extract_card_role_evidence(card),
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
                            card.select_one("a[data-testid='searchSerpJobTitle']") or
                             card.select_one("[data-testid='searchSerpJobTitle'] a[href]"))

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
                        "Posting_Date": posting_date,
                        "Description": safe_extract_card_role_evidence(card),
                    })
                    print(f"Scraped: {title_text} at {company_text}")

            except Exception as e:
                print(f"Error processing SimplyHired job card: {e}")
                continue

    return jobs

# Scrape job listings
def process_dice_from_browser(driver, search_country="N/A"):
    """Extract up to 20 distinct Dice jobs from rendered job cards."""
    dice_cards = driver.execute_script("""
        const clean = value =>
            String(value || "").replace(/\\s+/g, " ").trim();

        const cardEls = Array.from(
            document.querySelectorAll('[data-testid="job-card"]')
        );

        const seen = new Set();
        const result = [];

        for (const card of cardEls) {
            const titleLink = card.querySelector(
                '[data-testid="job-search-job-detail-link"]'
            );

            if (!titleLink) continue;

            const title = clean(titleLink.innerText);
            const link = clean(titleLink.href);

            if (!title || !link || seen.has(link)) continue;

            seen.add(link);

            const companyEl = card.querySelector(
                '[data-testid="job-card-company-name"]'
            );

            result.push({
                title: title,
                company: clean(companyEl && companyEl.innerText),
                location: "",
                postingDate: "",
                link: link,
                text: String(card.innerText || "").trim()
            });

            if (result.length >= 20) break;
        }

        return result;
    """)

    jobs = []
    seen_urls = set()

    print(f"Dice browser fallback found {len(dice_cards)} distinct card(s)")

    for card in dice_cards:
        title_text = card.get("title") or ""
        link_url = card.get("link") or ""

        if not title_text or not link_url or link_url in seen_urls:
            continue

        seen_urls.add(link_url)

        company_text = card.get("company") or "N/A"
        location_text = card.get("location") or "N/A"

        posting_date = (
            normalize_posting_date(card.get("postingDate"))
            if card.get("postingDate")
            else extract_posting_date_from_text(card.get("text"))
        )

        company_text, location_text, posting_date = parse_dice_card_text(
            title_text,
            card.get("text"),
            company_text,
            location_text,
            posting_date
        )

        location_text, posting_date = split_location_and_posting_date(
            location_text,
            posting_date
        )

        jobs.append({
            "Date_Found": datetime.now().strftime("%Y-%m-%d"),
            "Title": title_text,
            "Company": company_text,
            "Location": format_location(location_text, search_country),
            "Link": link_url,
            "Source": "Dice",
            "Posting_Date": posting_date,
            "Description": extract_role_evidence(card.get("text"))
        })

        print(
            f"Scraped from Dice browser fallback: "
            f"{title_text} at {company_text} ({posting_date})"
        )

    return jobs

def click_dice_filter_text(driver, text, timeout=8):
    """Click only supported Dice filter-panel buttons."""
    buttons = {
        "all filters": "All filters",
        "apply filters": "Apply filters",
    }

    target = buttons.get(text.lower())
    if target is None:
        return False

    xpath = "//button[normalize-space(.)=" + repr(target) + "]"

    try:
        button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            button
        )
        button.click()
        return True
    except Exception as exc:
        print(f"Dice button {target} failed: {type(exc).__name__}")
        return False


def ensure_dice_filter_selected(driver, selector, description, timeout=8):
    """Select a Dice filter at most once and verify its state."""
    deadline = time.monotonic() + timeout
    click_attempted = False

    def selected(label):
        if 'postedDateOption' in selector:
            return label.get_attribute("data-selected") == "true"

        if 'workPlaceTypeOptions.' in selector:
            inputs = label.find_elements(
                By.CSS_SELECTOR, 'input[type="checkbox"]'
            )
            return (
                len(inputs) == 1
                and inputs[0].get_property("checked") is True
            )

        return False

    while time.monotonic() < deadline:
        try:
            matches = driver.find_elements(By.CSS_SELECTOR, selector)

            if not matches:
                time.sleep(0.2)
                continue

            label = matches[0]

            if selected(label):
                print(f"Dice filter verified: {description}")
                return True

            if click_attempted:
                time.sleep(0.2)
                continue

            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                label
            )

            if not label.is_displayed() or not label.is_enabled():
                time.sleep(0.2)
                continue

            if 'workPlaceTypeOptions.' in selector:
                checkbox = label.find_element(
                    By.CSS_SELECTOR, 'input[type="checkbox"]'
                )

                driver.execute_script(
                    "arguments[0].focus();",
                    checkbox
                )

                focused = driver.execute_script(
                    "return document.activeElement === arguments[0];",
                    checkbox
                )

                if not focused:
                    print(f"Dice checkbox focus failed: {description}")
                    return False

                click_attempted = True
                ActionChains(driver).send_keys(Keys.SPACE).perform()

            else:
                click_attempted = True
                label.click()

        except Exception as exc:
            print(
                f"Dice filter retry {description}: "
                f"{type(exc).__name__}"
            )
            time.sleep(0.2)

    print(f"Dice filter timed out: {description}")
    return False


def verify_dice_filter_states(driver):
    """Verify all required selections before applying."""
    selectors = [
        'label:has(input[name="postedDateOption"][value="THREE"])',
        'label:has(input[name="workPlaceTypeOptions.remote"])',
        'label:has(input[name="workPlaceTypeOptions.hybrid"])',
    ]

    try:
        for selector in selectors:
            matches = driver.find_elements(By.CSS_SELECTOR, selector)

            if not matches:
                return False

            label = matches[0]

            if 'postedDateOption' in selector:
                if label.get_attribute("data-selected") != "true":
                    return False

            elif 'workPlaceTypeOptions.' in selector:
                inputs = label.find_elements(
                    By.CSS_SELECTOR, 'input[type="checkbox"]'
                )

                if (
                    len(inputs) != 1
                    or inputs[0].get_property("checked") is not True
                ):
                    return False

            else:
                return False

        return True

    except Exception:
        return False


def verify_dice_applied_url(url):
    """Verify the required Dice filters in the resulting URL."""
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    if parsed.hostname not in ("dice.com", "www.dice.com"):
        return False
    if parsed.path != "/jobs":
        return False

    params = parse_qs(parsed.query)

    if params.get("filters.postedDate") != ["THREE"]:
        return False

    workplace = params.get("filters.workplaceTypes", [])
    if len(workplace) != 1:
        return False

    values = workplace[0].split("|")
    selected = {value.strip().lower() for value in values}

    return (
        len(values) == 2
        and selected == {"remote", "hybrid"}
    )


def verify_dice_results_ready(driver, timeout=10):
    """Wait for Dice result elements after filter URL verification."""
    selector = (
        "dhi-search-result, "
        "[data-cy='card'], "
        "a[data-cy='card-title-link'], "
        "a[href*='/job-detail/'], "
        "a[href*='/jobs/detail/']"
    )

    try:
        WebDriverWait(driver, timeout).until(
            lambda d: (
                verify_dice_applied_url(d.current_url)
                and bool(d.find_elements(By.CSS_SELECTOR, selector))
            )
        )
        return True
    except Exception:
        print("Dice filtered results did not become ready.")
        return False


def apply_dice_filters(driver):
    """Apply Dice filters, verify URL, and wait for results."""
    print("Applying Dice filters: Last 3 days, Remote, Hybrid")

    if not click_dice_filter_text(driver, "all filters"):
        print("Could not open Dice filter drawer.")
        return False

    selectors = [
        (
            'label:has(input[name="postedDateOption"][value="THREE"])',
            "Last 3 days",
        ),
        (
            'label:has(input[name="workPlaceTypeOptions.remote"])',
            "Remote",
        ),
        (
            'label:has(input[name="workPlaceTypeOptions.hybrid"])',
            "Hybrid",
        ),
    ]

    for selector, description in selectors:
        if not ensure_dice_filter_selected(
            driver, selector, description
        ):
            print("Dice Apply filters skipped.")
            return False

    if not verify_dice_filter_states(driver):
        print("Dice pre-apply verification failed.")
        return False

    if not click_dice_filter_text(driver, "apply filters"):
        print("Dice Apply filters button failed.")
        return False

    try:
        WebDriverWait(driver, 10).until(
            lambda d: verify_dice_applied_url(d.current_url)
        )
    except Exception:
        print("Dice applied URL verification failed.")
        return False

    if not verify_dice_results_ready(driver):
        return False

    print("Dice filters and results verified.")
    return True

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


def extract_ziprecruiter_detail_date(driver, card_id, expected_title):
    """Read a selected ZipRecruiter job's date from its detail panel."""
    import re
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    try:
        card_selector = (
            "article[data-testid='" + card_id + "']"
        )

        card = driver.find_element(By.CSS_SELECTOR, card_selector)
        title_element = card.find_element(
            By.CSS_SELECTOR,
            "[data-testid='serp-job-card-title']"
        )

        panel_selector = "section[data-testid='job-details']"
        existing_panels = driver.find_elements(
            By.CSS_SELECTOR, panel_selector
        )
        previous_text = (
            existing_panels[0].text.strip()
            if existing_panels else None
        )

        # The first job may already be selected when the page loads.
        # Only trust its existing panel when the URL identifies this job.
        from urllib.parse import urlparse, parse_qs
        selected_id = parse_qs(
            urlparse(driver.current_url).query
        ).get("lk", [""])[0]

        if (
            selected_id == card_id.removeprefix("job-card-")
            and previous_text
            and expected_title.lower() in previous_text[:250].lower()
        ):
            match = re.search(
                r"\bposted\s+(today|yesterday|"
                r"\d+\s+(?:minutes?|hours?|days?|weeks?)\s+ago)\b",
                previous_text,
                flags=re.IGNORECASE
            )
            if match:
                return normalize_posting_date(match.group(0))

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            card
        )
        title_element.click()

        def matching_panel(browser):
            panels = browser.find_elements(
                By.CSS_SELECTOR, panel_selector
            )
            if not panels:
                return False

            text = panels[0].text.strip()

            if expected_title.lower() not in text[:250].lower():
                return False

            if previous_text is not None and text == previous_text:
                return False

            return text

        detail_text = WebDriverWait(driver, 15).until(
            matching_panel
        )

        match = re.search(
            r"\bposted\s+(today|yesterday|"
            r"\d+\s+(?:minutes?|hours?|days?|weeks?)\s+ago)\b",
            detail_text,
            flags=re.IGNORECASE
        )

        if match:
            return normalize_posting_date(match.group(0))

    except Exception as exc:
        print(
            f"ZipRecruiter detail date unavailable "
            f"for {card_id}: {type(exc).__name__}"
        )

    return "N/A"


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
            "Posting_Date": posting_date,
            "Description": extract_role_evidence(card.get("text"))
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
            "Posting_Date": posting_date,
            "Description": extract_role_evidence(card.get("text"))
        })
        print(f"Scraped from Indeed browser fallback: {title_text} at {company_text} ({posting_date})")

    return jobs

def get_source_ready_selector(source):
    """Return the CSS selector used to detect results for a job board."""
    selectors = {
        "LinkedIn": "[data-testid='job-search-result'], .jobs-search-results__list-item",
        "Indeed": "[data-jk], .job_seen_beacon",
        "Glassdoor": "[data-test='job-listing'], .react-job-listing",
        "ZipRecruiter": "[data-testid='job-card'], .jobList-item",
        "Dice": "dhi-search-result, [data-cy='card'], a[data-cy='card-title-link'], a[href*='/job-detail/'], a[href*='/jobs/detail/']",
        "SimplyHired": "[data-testid='searchSerpJob'], .SerpJob",
    }
    return selectors.get(source)

def page_looks_blocked(driver):
    """Detect common verification or access-blocking messages on a page."""
    text = f"{driver.title}\n{driver.page_source[:5000]}".lower()
    blocked_terms = [
        "captcha", "verify you are human", "verify it's you", "verify you",
        "unusual traffic", "security check", "are you a human",
        "access denied", "blocked", "robot", "humans only", "cloudflare",
        "just a moment"
    ]
    return any(term in text for term in blocked_terms)

def wait_for_manual_verification(driver, source, ready_selector):
    """Handle supported job-board verification prompts when detected."""
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
    """Attempt recovery when Indeed redirects to an auth or CORS page."""
    current_url = driver.current_url.lower()
    page_text = driver.page_source.lower()

    if "secure.indeed.com/auth" not in current_url and "invalid cors request" not in page_text:
        return False

    print("Indeed redirected to an auth/CORS page; returning to the search results URL.")
    driver.get(original_url)
    time.sleep(5)
    return True

def build_chrome_options(profile_path):
    """Configure Chrome options for the supplied browser profile."""
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
    """Create a Chrome WebDriver, with fallback profile handling."""
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
    """Visit configured job-board searches and collect job listings."""
    driver = create_chrome_driver()

    jobs = []

    try:
        # JOB_BOARDS maps each source to a LIST of URLs (one per country/region)
        for source, urls in JOB_BOARDS.items():
            if source in DISABLED_JOB_BOARDS:
                print(f"Skipping {source}: disabled because the site blocks automated scraping.")
                continue

            for url in urls:
                dice_filters_verified = False
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
                            EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid^='job-card-'], [data-testid='job-card'], .jobList-item"))
                        )
                        close_ziprecruiter_modal(driver)
                    elif source == "Dice":
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "dhi-search-result, [data-cy='card'], a[data-cy='card-title-link'], a[href*='/job-detail/'], a[href*='/jobs/detail/']")
                            )
                        )
                        time.sleep(3)
                        dice_filters_verified = apply_dice_filters(driver)
                    elif source == "SimplyHired":
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='searchSerpJob'], .SerpJob"))
                        )
                except Exception as e:
                    print(
                        f"Failed to load job listings from {source} ({url})\n"
                        f"Exception type: {type(e).__name__}\n"
                        f"Exception message: {e}"
                    )
                    verification_cleared = wait_for_manual_verification(driver, source, ready_selector)
                    if source == "Indeed":
                        recover_indeed_auth_redirect(driver, url)
                    if source == "Dice" and verification_cleared:
                        dice_filters_verified = apply_dice_filters(driver)
                    print("Continuing with available page content...")

                if source == "Dice" and not dice_filters_verified:
                    print("Skipping Dice search: filters not verified.")
                    continue

                soup = BeautifulSoup(driver.page_source, "html.parser")
                search_country = infer_country_from_url(url)
                jobs_found = process_job_board(soup, source, search_country, search_url=url)
                if source == "Indeed" and len(jobs_found) == 0:
                    jobs_found = process_indeed_from_browser(driver, search_country)
                if source == "ZipRecruiter" and len(jobs_found) == 0:
                    jobs_found = process_ziprecruiter_from_browser(driver, search_country)

                if source == "ZipRecruiter" and jobs_found:
                    from urllib.parse import urlparse, parse_qs

                    for job in jobs_found:
                        job_id = parse_qs(
                            urlparse(job.get("Link", "")).query
                        ).get("lk", [""])[0]

                        if not job_id:
                            continue

                        card_id = "job-card-" + job_id

                        posting_date = extract_ziprecruiter_detail_date(
                            driver,
                            card_id,
                            job.get("Title", "")
                        )

                        job["Posting_Date"] = posting_date

                        print(
                            f"ZipRecruiter date: {posting_date} | "
                            f"{job.get('Title', '')}"
                        )
                if source == "Dice" and len(jobs_found) == 0:
                    jobs_found = process_dice_from_browser(driver, search_country)
                if len(jobs_found) == 0:
                    print(f"⚠ WARNING: 0 jobs found on {source} for this URL. "
                          f"This usually means the site served a CAPTCHA/block page "
                          f"instead of real results, or its page structure changed.")
                if source == "Dice" and jobs_found:
                    from dice_browser_enrichment_candidate_v4 import (
                        enrich_dice_jobs,
                    )

                    jobs_found = enrich_dice_jobs(
                        driver,
                        jobs_found,
                        max_pages=20,
                        replace_card_evidence=True,
                    )

                jobs.extend(jobs_found)

    except Exception as e:
        if (
            isinstance(e, RuntimeError)
            and str(e) == "Dice browser state could not be restored"
        ):
            print(
                "CRITICAL: Dice browser restoration failed. "
                "Aborting scrape; partial results will not be returned."
            )
            raise

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
def resolve_posting_date(value, anchor=None):
    """Return (ISO date, confidence). Relative dates use discovery date."""
    anchor = pd.to_datetime(anchor, errors="coerce") if anchor is not None else pd.NaT

    if pd.isna(anchor):
        anchor = pd.Timestamp(datetime.now().date())

    anchor = anchor.normalize()

    if value is None or pd.isna(value) or str(value).strip().lower() in {
        "", "n/a", "nan", "none", "nat"
    }:
        return "N/A", "Unknown"

    text = str(value).strip().lower()

    if text in {"today", "just posted", "just now"}:
        return anchor.strftime("%Y-%m-%d"), "Estimated (relative)"

    if text == "yesterday":
        return (anchor - pd.Timedelta(days=1)).strftime("%Y-%m-%d"), "Estimated (relative)"

    match = re.fullmatch(
        r"(\d+)\s*(minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w)(?:\s+ago)?",
        text
    )

    if match:
        count, unit = int(match.group(1)), match.group(2)
        days = (
            count if unit in {"day", "days", "d"}
            else count * 7 if unit in {"week", "weeks", "wk", "wks", "w"}
            else 0
        )
        return (anchor - pd.Timedelta(days=days)).strftime("%Y-%m-%d"), "Estimated (relative)"

    try:
        parsed = pd.to_datetime(text, errors="raise")
        if pd.isna(parsed):
            return "N/A", "Unknown"
        return parsed.strftime("%Y-%m-%d"), "Reported (absolute)"
    except (ValueError, TypeError, OverflowError):
        return "N/A", "Unknown"
def row_verification_issues(row):
    """Identify job listings requiring manual verification."""
    issues = []

    posting = str(row.get("Posting_Date", "N/A")).strip()
    if posting in {"", "N/A", "nan", "NaT"}:
        issues.append("Posting date unknown")
    elif str(row.get("Posting_Date_Verified", "")).startswith("Estimated"):
        # Estimated relative dates are acceptable for recency checks.
        pass

    location = str(row.get("Location", "")).strip().lower()
    if location in {"", "n/a", "nan", "united states", "canada"}:
        issues.append("Specific location/work arrangement unknown")

    link = str(row.get("Link", "")).strip()
    if not link.startswith(("https://", "http://")):
        issues.append("Application link missing or invalid")

    return "; ".join(issues)
def row_is_within_age_limit(row):
    """Check a job row against the configured posting-age rules."""
    posting_date = row.get("Posting_Date", "N/A")
    if is_within_age_limit(posting_date):
        return True

    if str(row.get("Source", "")).lower() == "simplyhired":
        return is_within_age_limit(row.get("Date_Found", "N/A"))

    return False

def print_source_counts(label, df):
    """Print the number of jobs grouped by their source."""
    if df.empty or "Source" not in df.columns:
        print(f"{label}: 0 jobs")
        return

    counts = df["Source"].fillna("Unknown").value_counts().to_dict()
    formatted_counts = ", ".join(f"{source}: {count}" for source, count in counts.items())
    print(f"{label}: {formatted_counts}")

def clean_company_name_for_row(row):
    """Validate and clean company information for a job row."""
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
    """Upsert jobs, preserve original discovery dates and application decisions."""
    history = init_spreadsheet()
    today = datetime.now().strftime("%Y-%m-%d")
    for col in SPREADSHEET_COLUMNS:
        if col not in history.columns:
            history[col] = ""
    history = history.fillna("")
    # Migrate relative dates while preserving blank historical posting dates.
    for idx, row in history.iterrows():
        original = row.get("Posting_Date", "")
        original_text = (
            ""
            if pd.isna(original)
            else str(original).strip()
        )
        if original_text:
            resolved, confidence = resolve_posting_date(
                original, row.get("Date_Found")
            )
            history.at[idx, "Posting_Date"] = resolved
        else:
            confidence = "Unknown"
        if not str(row.get("Posting_Date_Verified", "")).strip():
            history.at[idx, "Posting_Date_Verified"] = confidence
        if not str(row.get("Last_Seen", "")).strip():
            history.at[idx, "Last_Seen"] = row.get("Date_Found", "")
        if not str(row.get("Application_Status", "")).strip():
            history.at[idx, "Application_Status"] = "Not Applied"

    incoming = pd.DataFrame(jobs)
    if incoming.empty:
        write_country_workbook(history)
        return pd.DataFrame(columns=SPREADSHEET_COLUMNS)
    rejected_titles = (~incoming["Title"].apply(is_relevant_title)).sum()
    print(f"Filtering: scraped={len(incoming)}, rejected non-software QA titles={rejected_titles}")
    incoming = incoming[incoming["Title"].apply(is_relevant_title)].copy()
    if incoming.empty:
        write_country_workbook(history)
        return pd.DataFrame(columns=SPREADSHEET_COLUMNS)
    incoming["Company"] = incoming.apply(clean_company_name_for_row, axis=1)

    # Classify from descriptions only; never infer industry from title.
    classification = incoming.apply(
        lambda row: classify_qa_job(row.get("Description", "")),
        axis=1,
        result_type="expand",
    )
    for col in (
        "QA_Category", "Classification_Evidence",
        "Software_Score", "Manufacturing_Score",
    ):
        incoming[col] = classification[col]
    for idx, row in incoming.iterrows():
        iso, confidence = resolve_posting_date(row.get("Posting_Date"), today)
        incoming.at[idx, "Posting_Date"] = iso
        incoming.at[idx, "Posting_Date_Verified"] = confidence
        incoming.at[idx, "Date_Found"] = today
        incoming.at[idx, "Last_Seen"] = today
        incoming.at[idx, "Application_Status"] = "Not Applied"
        incoming.at[idx, "Verification_Issue"] = row_verification_issues(incoming.loc[idx])

    def identity(row):
        return (normalize_text(row.get("Title")), normalize_company(row.get("Company")), normalize_location(row.get("Location")))

    history_keys = {identity(row): idx for idx, row in history.iterrows()}
    history_urls = {normalize_url(row.get("Link")): idx for idx, row in history.iterrows() if normalize_url(row.get("Link"))}
    new_rows = []
    duplicate_matches = 0
    for _, row in incoming.iterrows():
        key = identity(row)
        url = normalize_url(row.get("Link"))
        match_idx = history_keys.get(key)
        if match_idx is None and url:
            match_idx = history_urls.get(url)
        if match_idx is not None:
            duplicate_matches += 1
            history.at[match_idx, "Last_Seen"] = today
            # Upgrade previously missing fields without changing Date_Found/status.
            for col in ("Link", "Company", "Location", "Posting_Date", "Posting_Date_Verified"):
                old = str(history.at[match_idx, col]).strip()
                fresh = str(row.get(col, "")).strip()
                if old.lower() in {"", "n/a", "nan", "unknown"} and fresh.lower() not in {"", "n/a", "nan", "unknown"}:
                    history.at[match_idx, col] = fresh
            # Preserve existing descriptions; fill only missing values.
            old_description_value = history.at[
                match_idx, "Description"
            ]
            old_description = (
                ""
                if pd.isna(old_description_value)
                else str(old_description_value).strip()
            )

            fresh_description_value = row.get("Description", "")
            fresh_description = (
                fresh_description_value.strip()
                if isinstance(fresh_description_value, str)
                else ""
            )

            if not old_description and fresh_description:
                history.at[match_idx, "Description"] = fresh_description

            # Upgrade a blank legacy classification when a description is available.
            # Never overwrite an existing nonblank historical classification.
            existing_category_value = history.at[match_idx, "QA_Category"]
            existing_category = (
                ""
                if pd.isna(existing_category_value)
                else str(existing_category_value).strip()
            )

            description_for_classification = (
                old_description if old_description else fresh_description
            )

            if not existing_category and description_for_classification:
                upgraded_classification = classify_qa_job(
                    description_for_classification
                )
                for classification_column in (
                    "QA_Category",
                    "Classification_Evidence",
                    "Software_Score",
                    "Manufacturing_Score",
                ):
                    history.at[match_idx, classification_column] = (
                        upgraded_classification[classification_column]
                    )

            history.at[match_idx, "Verification_Issue"] = row_verification_issues(history.loc[match_idx])
        else:
            item = {col: row.get(col, "") for col in SPREADSHEET_COLUMNS}
            new_rows.append(item)
            idx = len(history)
            history = pd.concat([history, pd.DataFrame([item])], ignore_index=True)
            history_keys[key] = idx
            if url:
                history_urls[url] = idx
    print(f"Filtering: existing/duplicate matches={duplicate_matches}; new unique records={len(new_rows)}")
    write_country_workbook(history)
    new_df = pd.DataFrame(new_rows, columns=SPREADSHEET_COLUMNS)
    actionable = new_df[
        new_df.apply(
            lambda row: (
                row_is_within_age_limit(row)
                and not row_verification_issues(row)
                and str(row.get("QA_Category", "")).strip().casefold()
                == "software qa"
            ),
            axis=1,
        )
    ].copy() if not new_df.empty else new_df
    print(f"Scraped {len(jobs)}; new records={len(new_df)}; newly discovered recent actionable={len(actionable)}")
    return actionable

# Send email notification
def send_email(new_jobs):
    """Email newly discovered jobs when records and credentials are available."""
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
    """Coordinate scraping, processing, workbook updates, and notifications."""
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
    print("Daily scraping scheduled for 9:00 AM.")
    print("Keep this terminal running for automatic execution.")

    # Schedule daily task
    schedule.every().day.at("09:00").do(process_jobs)

    print("Scheduler is active. Waiting for the next scheduled run...")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nJob Tracker stopped by user.")