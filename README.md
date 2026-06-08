# QA Engineer Job Application Tracker

An automated job tracking system that scrapes job listings from multiple job boards, stores them in a spreadsheet, and can automatically apply to jobs.

## Features

- 🔍 **Multi-platform scraping**: LinkedIn, Indeed, and Glassdoor
- 📊 **Excel integration**: Stores job data in `job_opportunities.xlsx`
- 🤖 **Auto-apply functionality**: Automatically applies to jobs (simplified demo)
- 📧 **Email notifications**: Sends daily updates about new jobs found
- ⏰ **Scheduled execution**: Runs daily at 9:00 AM
- 🔄 **Duplicate detection**: Prevents duplicate job entries

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root with your email credentials:

```
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
RECIPIENT_EMAIL=recipient@gmail.com
```

**Note**: For Gmail, you'll need to use an App Password instead of your regular password. Enable 2FA and generate an App Password in your Google Account settings.

### 3. Chrome Browser

Make sure you have Google Chrome installed. The application uses ChromeDriver which will be automatically downloaded.

## Usage

### Run Once (Testing)

```bash
python job_tracker.py
```

This will:
1. Scrape jobs from all configured job boards
2. Save new jobs to the Excel spreadsheet
3. Attempt to auto-apply to unapplied jobs
4. Send an email notification if new jobs are found

### Run Tests

```bash
python test_tracker.py
```

### Add Sample Data (for testing)

```bash
python add_sample_data.py
```

## Configuration

### Job Boards

Edit the `JOB_BOARDS` dictionary in `job_tracker.py` to modify search URLs:

```python
JOB_BOARDS = {
    "LinkedIn": "https://www.linkedin.com/jobs/search/?keywords=QA%20Engineer&location=Remote",
    "Indeed": "https://www.indeed.com/jobs?q=QA+Engineer&l=Remote",
    "Glassdoor": "https://www.glassdoor.com/Job/remote-qa-engineer-jobs-SRCH_IL.0,6_IC1154532_KO7,18.htm"
}
```

### Schedule

The application is scheduled to run daily at 9:00 AM. Modify this in `job_tracker.py`:

```python
schedule.every().day.at("09:00").do(process_jobs)
```

## Files

- `job_tracker.py` - Main application
- `job_opportunities.xlsx` - Excel spreadsheet with job data
- `test_tracker.py` - Test suite
- `add_sample_data.py` - Utility to add sample data
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (create this)

## Important Notes

### Web Scraping Limitations

- **Rate Limiting**: Job boards may block requests if too frequent
- **Anti-bot Detection**: Some sites (especially LinkedIn) have sophisticated bot detection
- **Structure Changes**: Website layouts change frequently, requiring selector updates
- **Legal Considerations**: Always respect robots.txt and terms of service

### Auto-Apply Disclaimer

The auto-apply feature is a simplified demonstration. In practice:
- Most job applications require custom cover letters
- Many positions need specific qualifications review
- Some applications have multi-step processes
- Manual review is recommended before applying

### Email Security

- Use App Passwords for Gmail (not your regular password)
- Consider using environment variables or secure credential storage
- Never commit credentials to version control

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   - Ensure Chrome browser is installed
   - ChromeDriver is auto-downloaded by webdriver-manager

2. **Scraping Failures**
   - Job board layouts change frequently
   - Some sites block automated access
   - Try running with visible browser (remove headless mode)

3. **Email Issues**
   - Use App Password for Gmail
   - Check firewall/antivirus settings
   - Verify SMTP settings

### Debug Mode

To run with visible browser for debugging, modify the Chrome options in `scrape_jobs()`:

```python
options = Options()
# Comment out the headless option
# options.add_argument("--headless")
```

## Contributing

Feel free to:
- Add support for more job boards
- Improve scraping selectors
- Enhance the auto-apply functionality
- Add better error handling
- Improve the email templates

## Disclaimer

This tool is for educational and personal use only. Always respect website terms of service and use responsibly. The auto-apply feature should be used with caution and manual oversight.