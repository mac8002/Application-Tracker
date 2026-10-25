"""Standalone candidate for extracting Dice job descriptions.

No browser navigation, network requests, workbook access, or file writes.
"""

import json
import re

from bs4 import BeautifulSoup


DESCRIPTION_SELECTORS = (
    'div[class*="job-detail-description-module"][class*="jobDescription"]',
    '[data-testid="jobDescriptionHtml"]',
    '[data-testid="job-description"]',
    '[data-cy="jobDescription"]',
    '#jobDescription',
    '#job-description',
    '.job-description',
    '.jobDescription',
)

BLOCKED_PATTERNS = (
    "verify you are human",
    "checking your browser",
    "unusual traffic",
    "access denied",
    "captcha",
    "sign in to continue",
    "log in to continue",
)


def clean_description(value):
    """Convert HTML or plain text into readable description text."""
    if not isinstance(value, str):
        return ""

    soup = BeautifulSoup(value, "html.parser")

    for element in soup.select(
        "script, style, nav, footer, header, button, form"
    ):
        element.decompose()

    text = soup.get_text("\n", strip=True)
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
    ]

    cleaned = []
    previous = None

    for line in lines:
        if not line or line == previous:
            continue
        cleaned.append(line)
        previous = line

    return "\n".join(cleaned).strip()


def valid_description(value):
    """Apply conservative minimum-length and blocked-content checks."""
    if not isinstance(value, str):
        return False

    text = value.strip()

    if len(text) < 120:
        return False

    if len(text) > 100000:
        return False

    lower = text.lower()

    # Reject verification messages, not legitimate QA responsibilities.
    # A job description may legitimately mention testing CAPTCHA.
    blocked_openings = (
        "verify you are human",
        "checking your browser",
        "unusual traffic",
        "access denied",
        "sign in to continue",
        "log in to continue",
        "captcha verification required",
    )

    if lower.startswith(blocked_openings):
        return False

    return True


def is_jobposting_type(value):
    """Recognize JSON-LD JobPosting types."""
    if isinstance(value, str):
        return value.lower().split("/")[-1] == "jobposting"

    if isinstance(value, list):
        return any(is_jobposting_type(item) for item in value)

    return False


def iter_jsonld_objects(value):
    """Traverse JSON-LD objects, including arrays and @graph."""
    if isinstance(value, list):
        for item in value:
            yield from iter_jsonld_objects(item)

    elif isinstance(value, dict):
        yield value

        graph = value.get("@graph")
        if isinstance(graph, (list, dict)):
            yield from iter_jsonld_objects(graph)


def extract_dice_description(html):
    """Return a validated full description, or an empty string."""
    if not isinstance(html, str) or not html.strip():
        return ""

    soup = BeautifulSoup(html, "html.parser")

    page_title = (
        soup.title.get_text(" ", strip=True).lower()
        if soup.title
        else ""
    )

    if any(pattern in page_title for pattern in BLOCKED_PATTERNS):
        return ""

    # Prefer an explicitly identified job-description container.
    for selector in DESCRIPTION_SELECTORS:
        for element in soup.select(selector):
            candidate = clean_description(str(element))

            if valid_description(candidate):
                return candidate

    # Fallback: structured JobPosting data.
    for script in soup.select(
        'script[type="application/ld+json"]'
    ):
        raw = script.string or script.get_text()

        if not raw or not raw.strip():
            continue

        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue

        for obj in iter_jsonld_objects(data):
            if not is_jobposting_type(obj.get("@type")):
                continue

            candidate = clean_description(
                obj.get("description")
            )

            if valid_description(candidate):
                return candidate

    return ""
