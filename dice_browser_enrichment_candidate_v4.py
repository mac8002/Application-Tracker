"""Isolated Dice browser-enrichment candidate V3.

Does not create a browser or access Excel. Navigation occurs only
when enrich_dice_jobs() is called with a Selenium driver.
"""

import time
from urllib.parse import urljoin, urlparse

from dice_description_extractor_candidate_v3 import (
    extract_dice_description,
)

DICE_BASE_URL = "https://www.dice.com"
MAX_DETAIL_PAGES = 20
DETAIL_WAIT_SECONDS = 8
PAGE_LOAD_TIMEOUT_SECONDS = 15


def normalize_dice_url(value):
    if not isinstance(value, str):
        return ""

    value = value.strip()

    if not value or value.startswith("//"):
        return ""

    parsed_input = urlparse(value)

    if parsed_input.scheme and parsed_input.scheme.lower() != "https":
        return ""

    if not parsed_input.scheme and parsed_input.netloc:
        return ""

    url = urljoin(DICE_BASE_URL, value)
    parsed = urlparse(url)

    if parsed.scheme != "https":
        return ""

    if parsed.hostname not in ("dice.com", "www.dice.com"):
        return ""

    if parsed.username or parsed.password:
        return ""

    try:
        if parsed.port not in (None, 443):
            return ""
    except ValueError:
        return ""

    if not (
        parsed.path.startswith("/job-detail/")
        or parsed.path.startswith("/jobs/detail/")
    ):
        return ""

    if parsed.path.rstrip("/") in ("/job-detail", "/jobs/detail"):
        return ""

    return parsed._replace(fragment="").geturl()


def same_dice_detail_page(expected_url, actual_url):
    expected = normalize_dice_url(expected_url)
    actual = normalize_dice_url(actual_url)

    if not expected or not actual:
        return False

    return (
        urlparse(expected).path.rstrip("/")
        == urlparse(actual).path.rstrip("/")
    )


def enrich_dice_jobs(
    driver,
    jobs,
    max_pages=MAX_DETAIL_PAGES,
    replace_card_evidence=False,
):
    """Return enriched copies of jobs, leaving inputs unchanged.

    Set replace_card_evidence=True only when the caller knows
    that incoming Dice descriptions are card-level excerpts.
    """
    if not isinstance(jobs, list):
        raise TypeError("jobs must be a list")

    if not isinstance(max_pages, int) or isinstance(max_pages, bool):
        raise ValueError("max_pages must be an integer")

    if not 0 <= max_pages <= MAX_DETAIL_PAGES:
        raise ValueError("max_pages must be between 0 and 20")

    enriched = [dict(job) for job in jobs]

    if not enriched or max_pages == 0:
        return enriched

    original_handle = driver.current_window_handle
    original_timeout = driver.timeouts.page_load

    cache = {}
    visited = 0

    for job in enriched:
        if job.get("Source") != "Dice":
            continue

        existing = job.get("Description", "")

        if (
            isinstance(existing, str)
            and existing.strip()
            and not replace_card_evidence
        ):
            continue

        url = normalize_dice_url(job.get("Link", ""))

        if not url:
            continue

        if url in cache:
            if cache[url]:
                job["Description"] = cache[url]
            continue

        if visited >= max_pages:
            break

        visited += 1

        description = ""
        before_handles = set()
        owned_handle = None
        cleanup_failed = False
        timeout_changed = False

        try:
            driver.switch_to.window(original_handle)
            before_handles = set(driver.window_handles)

            driver.switch_to.new_window("tab")

            after_handles = set(driver.window_handles)
            new_handles = after_handles - before_handles

            if len(new_handles) != 1:
                raise RuntimeError(
                    "Cannot uniquely identify new Dice tab"
                )

            owned_handle = next(iter(new_handles))

            if driver.current_window_handle != owned_handle:
                raise RuntimeError(
                    "New Dice tab is not active"
                )

            driver.set_page_load_timeout(
                PAGE_LOAD_TIMEOUT_SECONDS
            )
            timeout_changed = True

            driver.get(url)

            deadline = time.monotonic() + DETAIL_WAIT_SECONDS

            while time.monotonic() < deadline:
                if not same_dice_detail_page(
                    url, driver.current_url
                ):
                    break

                description = extract_dice_description(
                    driver.page_source
                )

                if description:
                    break

                time.sleep(0.5)

            if description:
                job["Description"] = description

        except Exception as exc:
            print(
                "Dice detail extraction skipped for "
                f"{job.get('Title', 'Unknown')}: "
                f"{type(exc).__name__}: {exc}"
            )

        finally:
            try:
                if owned_handle is None and before_handles:
                    new_handles = (
                        set(driver.window_handles)
                        - before_handles
                    )

                    if len(new_handles) == 1:
                        owned_handle = next(iter(new_handles))

                    elif new_handles:
                        raise RuntimeError(
                            "Ambiguous newly created tabs"
                        )

                if (
                    owned_handle is not None
                    and owned_handle in driver.window_handles
                ):
                    driver.switch_to.window(owned_handle)
                    driver.close()

                if (
                    owned_handle is not None
                    and owned_handle in driver.window_handles
                ):
                    raise RuntimeError(
                        "Owned temporary tab remains open"
                    )

            except Exception as exc:
                cleanup_failed = True
                print(
                    "CRITICAL: Dice tab cleanup failed: "
                    f"{type(exc).__name__}: {exc}"
                )

            # Always attempt to restore the search tab, even if
            # temporary-tab cleanup failed or was ambiguous.
            try:
                driver.switch_to.window(original_handle)
            except Exception as exc:
                cleanup_failed = True
                print(
                    "CRITICAL: Search tab restoration failed: "
                    f"{type(exc).__name__}: {exc}"
                )

            if timeout_changed:
                try:
                    driver.set_page_load_timeout(
                        original_timeout
                    )
                except Exception as exc:
                    cleanup_failed = True
                    print(
                        "CRITICAL: Timeout restoration failed: "
                        f"{type(exc).__name__}: {exc}"
                    )

            if cleanup_failed:
                raise RuntimeError(
                    "Dice browser state could not be restored"
                )

        cache[url] = description

    return enriched
