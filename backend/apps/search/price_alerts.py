"""
Price drop detection — runs as a Celery async task after each scrape completes.
"""

import difflib
import logging
from decimal import Decimal

from celery import shared_task

from .utils import normalize_title

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    ignore_result=True,
)
def check_price_drops(self, search_id: int):
    """
    Celery task — compare new_search results against the previous search for
    the same user and query, then create or update PriceAlert records for any
    products whose price dropped.

    Dispatched with:  check_price_drops.delay(search.id)
    """
    try:
        from .models import PriceAlert, PriceThreshold, RawPrice, Search

        new_search = Search.objects.select_related("user").get(pk=search_id)
        user = new_search.user

        # 1. Find the most recent previous completed search for the same query
        previous_search = (
            Search.objects.filter(
                user=user,
                query__iexact=new_search.query,
                status=Search.Status.COMPLETED,
            )
            .exclude(pk=new_search.pk)
            .order_by("-created_at")
            .first()
        )

        if previous_search is None:
            logger.debug(
                "check_price_drops: no previous search found for query=%r (search_id=%s)",
                new_search.query,
                search_id,
            )
            return

        # 2. Fetch raw prices for both searches
        old_prices = list(RawPrice.objects.filter(search=previous_search))
        new_prices = list(RawPrice.objects.filter(search=new_search))

        if not old_prices or not new_prices:
            return

        # 3. Build normalised-title → RawPrice dict for old results
        old_map: dict[str, RawPrice] = {}
        for p in old_prices:
            old_map[normalize_title(p.title)] = p

        alerts_created = 0
        alerts_updated = 0

        # 4. Match and detect drops
        for new_item in new_prices:
            norm_new = normalize_title(new_item.title)

            # Exact match first
            old_item = old_map.get(norm_new)

            # Fuzzy fallback (>0.85 similarity)
            if old_item is None:
                best_ratio = 0.0
                best_key = None
                for old_key in old_map:
                    ratio = difflib.SequenceMatcher(None, old_key, norm_new).ratio()
                    if ratio > 0.85 and ratio > best_ratio:
                        best_ratio = ratio
                        best_key = old_key
                if best_key:
                    old_item = old_map[best_key]

            if old_item is None:
                continue

            # 5. Calculate prices in MAD
            old_price_mad = Decimal(str(float(old_item.price) * old_item.exchange_rate))
            new_price_mad = Decimal(str(float(new_item.price) * new_item.exchange_rate))

            # Skip if no real drop (< 1 MAD threshold to filter float noise)
            if new_price_mad >= old_price_mad:
                continue
            drop_amount = old_price_mad - new_price_mad
            if drop_amount < Decimal("1.00"):
                continue

            drop_percent = (drop_amount / old_price_mad) * Decimal("100")

            alert_data = dict(
                old_price=old_price_mad.quantize(Decimal("0.01")),
                new_price=new_price_mad.quantize(Decimal("0.01")),
                drop_amount=drop_amount.quantize(Decimal("0.01")),
                drop_percent=drop_percent.quantize(Decimal("0.1")),
                platform=new_item.platform,
                product_url=new_item.url,
            )

            # 6. Upsert — keep only one unread alert per product + query
            existing = PriceAlert.objects.filter(
                user=user,
                product_title=new_item.title,
                search_query__iexact=new_search.query,
                is_read=False,
                is_threshold_alert=False,
            ).first()

            if existing:
                existing.delete()
                alerts_updated += 1
            else:
                alerts_created += 1

            PriceAlert.objects.create(
                user=user,
                product_title=new_item.title,
                search_query=new_search.query,
                is_read=False,
                is_threshold_alert=False,
                **alert_data,
            )

            # 7. Threshold alert — check if the new price hit the user's target
            threshold = PriceThreshold.objects.filter(
                user=user,
                normalized_title=norm_new,
                platform=new_item.platform,
            ).first()

            if threshold and new_price_mad <= threshold.threshold_mad:
                existing_ta = PriceAlert.objects.filter(
                    user=user,
                    product_title=new_item.title,
                    search_query__iexact=new_search.query,
                    is_read=False,
                    is_threshold_alert=True,
                ).first()
                if existing_ta:
                    existing_ta.delete()

                PriceAlert.objects.create(
                    user=user,
                    product_title=new_item.title,
                    search_query=new_search.query,
                    is_read=False,
                    is_threshold_alert=True,
                    **alert_data,
                )

        logger.info(
            "check_price_drops done for search_id=%s query=%r — created=%d updated=%d",
            search_id,
            new_search.query,
            alerts_created,
            alerts_updated,
        )

        # Push real-time notification to user's open browser tabs
        if alerts_created + alerts_updated > 0:
            from apps.ws.utils import notify_alert_ws
            unread_count = PriceAlert.objects.filter(user=user, is_read=False).count()
            notify_alert_ws(user.id, unread_count)

    except Exception as exc:
        logger.exception("check_price_drops failed for search_id=%s", search_id)
        raise self.retry(exc=exc)
