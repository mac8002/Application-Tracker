# QA Engineer Job Application Tracker

A Python/Selenium job-discovery and Excel tracking tool for software QA, testing, and automation roles in the United States and Canada. It gathers job listings, filters unrelated titles, maintains job history, and organizes opportunities for **manual review and application**.

> **Version 4:** This tool does **not** submit job applications automatically. Job-board pages and posting dates may be incomplete, and a search result is not proof of location or work authorization eligibility.

## Features

- **Multiple job boards:** LinkedIn, Indeed, Dice, and SimplyHired. Glassdoor and ZipRecruiter are currently disabled due to scraping restrictions or unreliable results.
- **Software QA title filtering:** Excludes many manufacturing, construction, structural, and other non-software quality positions. Filtering is heuristic; review results before applying.
- **History and duplicate handling:** Retains previously discovered jobs, records last-seen dates, and deduplicates shortlist views.
- **Date-aware review:** Separates postings with recognizable recent dates from jobs discovered recently whose original posting dates may be unknown.
- **Remote/hybrid review:** Separates likely U.S. remote listings, uncertain remote eligibility, and U.S. hybrid listings. Always confirm eligibility in the original posting.
- **Optional email notifications:** Attempts to notify you about newly discovered actionable listings. Email delivery depends on valid SMTP settings and network access.
- **Scheduling while running:** Executes once at startup and again daily at 9:00 AM **local computer time**, provided the Python process remains open.

## Requirements

- Python 3.10+ recommended
- Google Chrome
- Internet connection
- Python packages listed in `requirements.txt`

Create or update `requirements.txt` with:

```text
beautifulsoup4
pandas
openpyxl
python-dotenv
schedule
selenium
webdriver-manager
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

ChromeDriver is managed using `webdriver-manager`. Some job boards may present verification challenges that require interaction in the browser.

## Configuration

Create a `.env` file alongside `job_tracker.py`:

```dotenv
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
RECIPIENT_EMAIL=recipient@gmail.com
```

Use a Gmail App Password where supported, not your main account password. **Never commit `.env` or personal job-tracking data to GitHub.** Email notifications are optional; the workbook can still be updated if email is not configured.

The main settings are near the top of `job_tracker.py`:

- `JOB_BOARDS`: lists of search URLs for U.S. and Canadian QA Engineer / QA Analyst searches.
- `DISABLED_JOB_BOARDS`: sources intentionally skipped (currently Glassdoor and ZipRecruiter).
- `MAX_JOB_AGE_DAYS = 3`: today plus the previous three calendar days.
- `KEEP_UNDATED_JOBS_FOR_REVIEW`: preserves records with missing dates for manual review.
- `SPREADSHEET_PATH`: `job_opportunities.xlsx` in the same directory as the script.

## Run

The release script should be named `job_tracker.py`. If testing the downloaded v4 file without renaming it, run `python job_tracker_v4.py` instead.

```powershell
python job_tracker.py
```

The script runs **immediately**, then stays active and checks for the next 9:00 AM scheduled run. Press **Ctrl+C** to stop it. If you close the terminal or shut down the computer, it will not run automatically the next day. For unattended runs, configure Windows Task Scheduler separately and avoid running multiple copies simultaneously.

**Back up `job_opportunities.xlsx` before testing a new script version.** The workbook is rewritten when refreshed; it is not a database or an external backup.

## Excel worksheets

| Worksheet | Purpose |
|---|---|
| `New - Last 3 Days` | Relevant listings with recognizable recent posting dates and no flagged verification issues. |
| `Newly Discovered` | Relevant listings first found within the lookback window and containing a plausible job URL; the posting date may be older or unknown. |
| `US Remote - Review` | Remote candidates from U.S. search results; U.S. eligibility still requires confirmation. |
| `Remote Eligibility Check` | Remote listings whose country/eligibility is uncertain or not classified as U.S. search results. |
| `US Hybrid` | U.S. hybrid candidates for review. |
| `Needs Verification` | Recently discovered listings with missing or questionable details. |
| `All Jobs - History` | Historical records, including dates, status, and previously seen jobs. |
| `United States` / `Canada` | Country-oriented views based on parsed listing location. |

**Date definitions:** `Posting_Date` describes when the listing appears to have been posted; `Date_Found` is when this tracker first encountered it; `Last_Seen` is the latest observation. An unknown posting date is **not** treated as a verified new posting. Relative dates such as “Today” are interpreted when scraped.

**Important:** A syntactically valid URL is not proof that the job page is active or matches the recorded role. Open the original listing and verify posting date, employer, work arrangement, and application eligibility before applying.

## Troubleshooting

**LinkedIn / Dice Selenium timeouts:** The tracker may log a timeout and then continue using available rendered page content. Check the final counts rather than treating every timeout as a complete scrape failure.

**Indeed verification:** Indeed may request a browser challenge. Complete it manually if prompted. Some Indeed results may have `N/A` posting dates.

**Zero results from a board:** The site may have changed its layout or blocked automation. Glassdoor and ZipRecruiter are currently disabled.

**Irrelevant results:** Search results may include non-software quality roles. The title filter reduces noise but is not a substitute for reviewing descriptions.

**SMTP `Connection unexpectedly closed`:** Email sending has not yet been validated successfully. Check connectivity, SMTP access, Gmail App Password configuration, and security software. Do not paste credentials into issue reports or chat logs.

**Duplicate-looking records:** The historical sheet may retain distinct source records, while shortlist sheets are deduplicated. Review potential false matches before changing history.

## Repository files

- `job_tracker.py` — main script (use the tested v4 code under this filename when releasing)
- `requirements.txt` — Python dependencies
- `README.md` — documentation
- `.gitignore` — excludes secrets, local Chrome profile, caches, and personal workbook data
- `job_opportunities.xlsx` — generated locally; **do not commit**
- `.env` — local credentials; **do not commit**

Older helper files such as `test_tracker.py` and `add_sample_data.py` may exist in the repository, but their compatibility with v4 has not been verified.

## Responsible use

This project is intended for personal job discovery. Respect job-board terms, rate limits, and access restrictions. Do not bypass verification or anti-bot protections. Apply manually after reviewing each job and its requirements.
