import logging

from celery import shared_task
from django.db import transaction

from apps.search.models import (
    AnalysisResult,
    AssociationRule,
    RawPrice,
    Search,
    SearchAnalysis,
)
from apps.ws.utils import notify_ws
from mining.pipeline import run_mining_pipeline
from scraper.dispatcher import scrape_all
from scraper.exchange_rate import get_exchange_rate

logger = logging.getLogger(__name__)

FALLBACK_RATES = {
    "MAD": 1.0,
    "EUR": 11.0,
    "USD": 10.0,
}


@shared_task(
    bind=True,
    time_limit=300,
    soft_time_limit=270,
    max_retries=2,
)
def run_search_pipeline(self, search_id):
    """Orchestrate scrape → mine → atomic save for a Search."""
    # Step 1: mark as processing
    search = Search.objects.get(pk=search_id)
    search.status = Search.Status.PROCESSING
    search.save(update_fields=["status"])
    notify_ws(search_id, "status", {"status": "processing"})

    try:
        # Step 2: get exchange rates
        try:
            rates = get_exchange_rate(timeout=5)
        except Exception:
            logger.warning("Failed to fetch exchange rates, using fallback dict.")
            rates = FALLBACK_RATES.copy()

        # Step 3: scrape all requested platforms
        dispatch_result = scrape_all(search.query, search.platforms, search_id)

        # Handle both dict {"results": [...]} and direct list returns
        if isinstance(dispatch_result, dict):
            scraped_items = dispatch_result.get("results", [])
        elif isinstance(dispatch_result, list):
            scraped_items = dispatch_result
        else:
            scraped_items = []

        if not scraped_items:
            logger.warning("No items scraped for search %s", search_id)

        # Build RawPrice objects from scraped data
        raw_price_objects = []
        for item in scraped_items:
            currency = item.get("currency", "MAD")
            rate = rates.get(currency, 1.0)
            raw_price_objects.append(
                RawPrice(
                    search=search,
                    platform=item["platform"],
                    title=item["title"],
                    price=item["price"],
                    currency=currency,
                    exchange_rate=rate,
                    url=item["url"],
                    seller_rating=item.get("rating"),
                    condition=item.get("condition"),
                )
            )

        # Step 4: atomic save + mine
        with transaction.atomic():
            RawPrice.objects.bulk_create(
                raw_price_objects, ignore_conflicts=True
            )

            # Re-query to obtain PKs for downstream analysis
            saved_raw_prices = list(
                RawPrice.objects.filter(search=search)
            )

            # Run mining pipeline on saved prices
            notify_ws(search_id, "mining", {})
            pipeline_result = run_mining_pipeline(saved_raw_prices)

            # Bulk create analysis results from pipeline output
            analysis_objects = pipeline_result.analysis_results
            if analysis_objects:
                AnalysisResult.objects.bulk_create(analysis_objects)

            # Persist aggregated search analysis
            SearchAnalysis.objects.create(
                search=search,
                stats=pipeline_result.stats,
                best_deal_id=pipeline_result.best_deal_id,
            )

            # Bulk create association rules from pipeline output
            rule_objects = pipeline_result.association_rules
            if rule_objects:
                AssociationRule.objects.bulk_create(rule_objects)

        # Step 5: mark completed
        search.status = Search.Status.COMPLETED
        search.save()

        # WebSocket notification sent AFTER atomic block closes
        notify_ws(search_id, "done", {})

    except Exception as exc:
        logger.exception("Pipeline failed for search %s", search_id)

        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc,
                countdown=30 * (2 ** self.request.retries),
            )

        # Final failure — no more retries
        search.status = Search.Status.FAILED
        search.save()
        notify_ws(search_id, "error", {"message": str(exc)})
        raise
