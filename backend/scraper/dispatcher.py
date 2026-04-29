import logging
from typing import Any

from .base import close_browser, get_browser
from .jumia import scrape_jumia

logger = logging.getLogger(__name__)

# Map platform names to their respective scraping functions
SCRAPER_MAP = {
    "jumia": scrape_jumia,
}

def scrape_all(query: str, platforms: list[str]) -> list[dict[str, Any]]:
    """
    Dispatch scraping tasks to multiple platforms and collect results.
    """
    results = []
    browser = get_browser()

    try:
        for platform in platforms:
            platform_lower = platform.lower()
            if platform_lower in SCRAPER_MAP:
                logger.info(f"Starting scrape for platform: {platform_lower}")
                try:
                    scraper_func = SCRAPER_MAP[platform_lower]
                    platform_results = scraper_func(query, browser)
                    results.extend(platform_results)
                    logger.info(f"Finished {platform_lower}: found {len(platform_results)} items")
                except Exception:
                    logger.exception(f"Failed to scrape platform: {platform_lower}")
            else:
                logger.warning(f"No scraper implemented for platform: {platform}")

        return results
    finally:
        # We close the browser after all requested platforms are done
        # to ensure cleanup in the Celery worker process.
        close_browser()
