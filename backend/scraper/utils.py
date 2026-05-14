from __future__ import annotations

import random
import time

from .user_agents import USER_AGENTS


def get_random_ua() -> str:
    """Return a random user agent string."""
    return random.choice(USER_AGENTS)


def random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """Sleep for a random duration between min_s and max_s seconds."""
    time.sleep(random.uniform(min_s, max_s))


def clean_price(text: str | None) -> float | None:
    """
    Strip currency symbols, commas, and whitespace from a price string
    and return a float. Returns None if parsing fails.

    Examples:
        "2,753.13 MAD" -> 2753.13
        "DH 388"       -> 388.0
        "1.299,00 €"   -> 1299.0
        ""             -> None
    """
    if not text:
        return None

    cleaned = text.strip()

    # Strip known currency tokens
    for token in ("MAD", "Dhs", "DHS", "DH", "EUR", "USD", "GBP", "€", "$", "£"):
        cleaned = cleaned.replace(token, "")

    # Keep only digits, commas, and dots
    cleaned = "".join(ch for ch in cleaned if ch.isdigit() or ch in ",.")
    cleaned = cleaned.strip()

    if not cleaned:
        return None

    # Disambiguate decimal vs thousands separators
    if "," in cleaned and "." in cleaned:
        # Whichever comes last is the decimal separator
        if cleaned.rfind(".") > cleaned.rfind(","):
            # e.g. "1,299.00" — comma is thousands
            cleaned = cleaned.replace(",", "")
        else:
            # e.g. "1.299,00" — dot is thousands, comma is decimal
            cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        tail = cleaned.rsplit(",", 1)[-1]
        if len(tail) == 2:
            # e.g. "2,75" — comma is decimal separator
            cleaned = cleaned.replace(",", ".")
        else:
            # e.g. "2,753" — comma is thousands separator
            cleaned = cleaned.replace(",", "")
    elif "." in cleaned:
        tail = cleaned.rsplit(".", 1)[-1]
        if len(tail) == 3:
            # e.g. "2.753" — dot is thousands separator
            cleaned = cleaned.replace(".", "")

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None