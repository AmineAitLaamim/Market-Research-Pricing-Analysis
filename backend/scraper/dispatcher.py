import logging
from typing import Any

from .base import close_browser, get_browser
from .jumia import scrape_jumia
from apps.ws.utils import notify_ws

logger = logging.getLogger(__name__)

# Map platform names to their respective scraping functions
SCRAPER_MAP = {
    "jumia": scrape_jumia,
}

def scrape_all(query: str, platforms: list[str], search_id: int | None = None) -> list[dict[str, Any]]:
    """
    Dispatch scraping tasks to multiple platforms and collect results.
    """
    results = []
    browser = get_browser()
    try:
        def progress_callback(platform: str, item_count: int):
            if search_id:
                notify_ws(search_id, "scraping", {"platform": platform, "count": item_count})

        for platform in platforms:
            platform_lower = platform.lower()
            if platform_lower in SCRAPER_MAP:
                logger.info(f"Starting scrape for platform: {platform_lower}")
                progress_callback(platform_lower, 0)
                try:
                    scraper_func = SCRAPER_MAP[platform_lower]
                    platform_results = scraper_func(query, browser, progress_callback)
                    results.extend(platform_results)
                    logger.info(f"Finished {platform_lower}: found {len(platform_results)} items")
                    progress_callback(platform_lower, len(platform_results))
                except Exception:
                    logger.exception(f"Failed to scrape platform: {platform_lower}")
            else:
                logger.warning(f"No scraper implemented for platform: {platform}")

        return results
    finally:
        # We close the browser after all requested platforms are done
        # to ensure cleanup in the Celery worker process.
        close_browser()
