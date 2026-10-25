import re
from bs4 import BeautifulSoup
from qa_description_extractor import extract_role_evidence


def filter_metadata(evidence):
    clean = []

    for raw_line in (evidence or "").splitlines():
        line = raw_line.strip()
        lower = line.lower()

        if not line:
            continue

        if lower in {
            "remote", "hybrid", "onsite",
            "on-site", "work from home",
        }:
            continue

        if re.match(
            r"^(posted|listed|updated)\s*:?\s*"
            r"(\d+|today|yesterday|just)",
            lower,
        ):
            continue

        if re.fullmatch(
            r"\$\s*[\d,]+(?:\.\d+)?\s*[kKmM]?"
            r"(?:\s*[-?]\s*\$?\s*[\d,]+(?:\.\d+)?\s*[kKmM]?)?"
            r"(?:\s*(?:per\s+(?:hour|year)|/"
            r"(?:hr|hour|year)|hourly|annually|annual))?",
            line,
            re.IGNORECASE,
        ):
            continue

        if re.match(
            r"^(company industry|industry|company size)\s*:",
            lower,
        ):
            continue

        company_intro = re.match(
            r"^(we are|we're|our company is)\s+"
            r"(?:a|an|the)\s+"
            r"(?:leading|global|innovative|established)\b",
            lower,
        )

        if company_intro:
            qa_responsibility = re.search(
                r"\b("
                r"testing|tests|test cases|test automation|"
                r"quality assurance|qa team|"
                r"selenium|playwright|appium|"
                r"api testing|regression testing|"
                r"inspect|inspection|validation|"
                r"validate|verifying|verify"
                r")\b",
                lower,
            )

            if qa_responsibility is None:
                continue
        clean.append(line)

    return "\n".join(clean)


def extract_card_role_evidence(card):
    """Extract explicit role evidence from a BeautifulSoup job card."""
    if card is None:
        return ""

    structured_text = card.get_text("\n", strip=True)
    evidence = extract_role_evidence(structured_text)

    return filter_metadata(evidence)
