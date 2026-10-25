"""Conservative extraction of QA role evidence from listing text."""

import re

ROLE_HEADINGS = {
    "responsibilities",
    "key responsibilities",
    "requirements",
    "job requirements",
    "qualifications",
    "job duties",
    "what you will do",
}

STOP_HEADINGS = {
    "about us",
    "about the company",
    "company overview",
    "company background",
    "benefits",
    "compensation",
    "equal opportunity",
    "how to apply",
    "job overview",
    "job summary",
    "who we are",
    "our mission",
    "our culture",
    "why join us",
    "company information",
}


def clean_heading(line):
    return re.sub(
        r"^[#*\s-]+|[:\s*]+$",
        "",
        line.strip().lower(),
    )


def is_unknown_heading(line):
    stripped = line.strip()

    if not stripped:
        return False

    if re.match(r"^#{1,6}\s+\S+", stripped):
        return True

    if stripped.endswith(":") and len(stripped) <= 60:
        return True

    return False


def extract_role_evidence(card_text):
    """Extract explicitly labeled role duties or requirements.

    Returns an empty string when reliable evidence is unavailable.
    Does not classify jobs or access external resources.
    """
    if not isinstance(card_text, str):
        return ""

    selected = []
    collecting = False

    for raw_line in card_text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        heading = clean_heading(line)

        if heading in ROLE_HEADINGS:
            collecting = True
            continue

        if heading in STOP_HEADINGS:
            collecting = False
            continue

        inline = re.match(
            r"^(responsibilities|key responsibilities|"
            r"requirements|job requirements|qualifications|"
            r"job duties|what you will do)\s*:\s*(.+)$",
            line,
            re.IGNORECASE,
        )

        if inline:
            collecting = True
            selected.append(inline.group(2).strip())
            continue

        if is_unknown_heading(line):
            collecting = False
            continue

        if collecting:
            selected.append(line)

    return "\n".join(selected).strip()
