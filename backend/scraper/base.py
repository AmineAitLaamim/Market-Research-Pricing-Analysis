from __future__ import annotations

import os
import random

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from playwright_stealth.stealth import Stealth

from .utils import clean_price, get_random_ua


_playwright: Playwright | None = None
_browser: Browser | None = None

_VIEWPORTS = (
    {"width": 1280, "height": 720},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1920, "height": 1080},
)

_LOCALES = ["en-US", "en-GB", "fr-FR", "en-CA", "fr-MA"]

_TIMEZONES = [
    "Africa/Casablanca",
    "Europe/Paris",
    "Europe/London",
    "America/New_York",
    "America/Toronto",
]

_SEC_CH_UA_MAP = {
    "Chrome/124": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Chrome/123": '"Chromium";v="123", "Google Chrome";v="123", "Not-A.Brand";v="99"',
    "Chrome/122": '"Chromium";v="122", "Google Chrome";v="122", "Not-A.Brand";v="99"',
    "Edg/124":    '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
    "Edg/123":    '"Chromium";v="123", "Microsoft Edge";v="123", "Not-A.Brand";v="99"',
}

# SCRAPER_HEADLESS=false disables headless mode, which greatly reduces
# detection. Useful during development or when CAPTCHAs are encountered.
_HEADLESS = os.environ.get("SCRAPER_HEADLESS", "true").lower() != "false"


def _get_sec_ch_ua(user_agent: str) -> str | None:
    for key, value in _SEC_CH_UA_MAP.items():
        if key in user_agent:
            return value
    return None


def _get_platform(user_agent: str) -> str:
    if "Windows" in user_agent:
        return "Windows"
    if "Macintosh" in user_agent:
        return "macOS"
    return "Linux"


def get_browser() -> Browser:
    global _playwright, _browser

    if _browser is None:
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(
            headless=_HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                # Keep extensions disabled but don't pass --disable-extensions
                # as some stealth patches rely on the extension API shape.
            ],
        )

    return _browser


def apply_stealth(page: Page) -> None:
    """Apply playwright-stealth to a single page.

    playwright-stealth patches 30+ fingerprinting signals:
    navigator.webdriver, chrome runtime object, hairline feature,
    WebGL vendor/renderer, permission API, plugin array, etc.
    """
    Stealth().apply_stealth_sync(page)


def create_context(browser: Browser) -> BrowserContext:
    """
    Creates a fresh browser context with a fully randomized fingerprint.
    Every call produces a different UA, viewport, locale, timezone, and
    headers — making consecutive scrapes look like different users.
    """
    user_agent = get_random_ua()
    viewport   = random.choice(_VIEWPORTS)
    locale     = random.choice(_LOCALES)
    timezone   = random.choice(_TIMEZONES)
    sec_ch_ua  = _get_sec_ch_ua(user_agent)
    platform   = _get_platform(user_agent)

    extra_headers: dict[str, str] = {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language":           f"{locale},{locale.split('-')[0]};q=0.9,en;q=0.8",
        "Accept-Encoding":           "gzip, deflate, br",
        "DNT":                       "1",
        "Upgrade-Insecure-Requests": "1",
    }

    # Only Chromium-based UAs send sec-ch-* headers
    # Adding them to Firefox/Safari fingerprints would be inconsistent
    if sec_ch_ua:
        extra_headers.update({
            "sec-ch-ua":          sec_ch_ua,
            "sec-ch-ua-mobile":   "?0",
            "sec-ch-ua-platform": f'"{platform}"',
            "Sec-Fetch-Dest":     "document",
            "Sec-Fetch-Mode":     "navigate",
            "Sec-Fetch-Site":     "none",
            "Sec-Fetch-User":     "?1",
        })

    context = browser.new_context(
        user_agent=user_agent,
        viewport=viewport,
        locale=locale,
        timezone_id=timezone,
        extra_http_headers=extra_headers,
        color_scheme=random.choice(["light", "dark"]),
        java_script_enabled=True,
    )

    return context


def parse_price_string(text: str | None) -> float | None:
    """Delegate to clean_price for backward compatibility."""
    return clean_price(text)


def close_browser() -> None:
    global _playwright, _browser

    if _browser is not None:
        _browser.close()
        _browser = None

    if _playwright is not None:
        _playwright.stop()
        _playwright = None
