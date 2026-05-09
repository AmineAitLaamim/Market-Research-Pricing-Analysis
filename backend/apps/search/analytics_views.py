"""
Product Intelligence analytics views.
Mounted at /api/analytics/ in the main URL config.
"""

import difflib
import statistics
from collections import Counter
from decimal import Decimal

from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import PriceAlert, PriceThreshold, RawPrice, Search
from .utils import normalize_title


class TopDropsView(generics.GenericAPIView):
    """Return the 6 products with the biggest price drops (current vs max historical) for the user."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        qs = RawPrice.objects.filter(search__user=request.user).order_by("scraped_at")
        
        # Group by normalized title + platform
        grouped = {}
        for p in qs.iterator():
            norm = normalize_title(p.title)
            key = (norm, p.platform)
            if key not in grouped:
                grouped[key] = {
                    "title": p.title,
                    "normalized_title": norm,
                    "platform": p.platform,
                    "prices": [],
                    "dates": [],
                    "image_url": None,
                }
            grouped[key]["prices"].append(float(p.price) * p.exchange_rate)
            grouped[key]["dates"].append(p.scraped_at)
            if p.image_url:
                grouped[key]["image_url"] = p.image_url

        drops = []
        for key, data in grouped.items():
            if len(data["prices"]) < 2:
                continue
                
            latest_price = data["prices"][-1]
            # Max price before the latest scrape
            max_price = max(data["prices"][:-1])
            
            if latest_price < max_price:
                drop_amount = max_price - latest_price
                # Filter out negligible drops (< 1 MAD)
                if drop_amount >= 1.0:
                    drop_percent = (drop_amount / max_price) * 100
                    drops.append({
                        "title": data["title"],
                        "normalized_title": data["normalized_title"],
                        "platform": data["platform"],
                        "image_url": data["image_url"],
                        "latest_price_mad": round(latest_price, 2),
                        "old_price_mad": round(max_price, 2),
                        "drop_amount": round(drop_amount, 2),
                        "drop_percent": round(drop_percent, 1),
                        "last_scraped": data["dates"][-1].isoformat(),
                    })
                    
        # Sort by drop amount descending
        drops.sort(key=lambda x: x["drop_amount"], reverse=True)
        return Response(drops)


class ProductSearchView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        q = request.query_params.get("q", "").strip()

        qs = RawPrice.objects.filter(search__user=request.user).select_related("search")

        if len(q) >= 2:
            qs = qs.filter(title__icontains=q)
        else:
            # Return 6 most recent unique products
            qs = qs.order_by("-scraped_at")

        # Group by normalized title + platform
        grouped = {}
        for p in qs.iterator():
            key = (normalize_title(p.title), p.platform)
            if key not in grouped:
                grouped[key] = {
                    "titles": [],
                    "platform": p.platform,
                    "normalized_title": key[0],
                    "prices": [],
                    "dates": [],
                }
            grouped[key]["titles"].append(p.title)
            grouped[key]["prices"].append(float(p.price) * p.exchange_rate)
            grouped[key]["dates"].append(p.scraped_at)

        results = []
        for key, data in grouped.items():
            title_counter = Counter(data["titles"])
            most_common_title = title_counter.most_common(1)[0][0]
            latest_idx = data["dates"].index(max(data["dates"]))
            results.append({
                "title": most_common_title,
                "normalized_title": data["normalized_title"],
                "platform": data["platform"],
                "scrape_count": len(data["titles"]),
                "latest_price_mad": round(data["prices"][latest_idx], 2),
                "last_scraped": max(data["dates"]).isoformat(),
            })

        results.sort(key=lambda x: x["last_scraped"], reverse=True)
        limit = 10 if len(q) >= 2 else 6
        return Response(results[:limit])


class ProductHistoryView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        title_q = request.query_params.get("title", "").strip()
        platform_q = request.query_params.get("platform", "").strip()

        if not title_q or not platform_q:
            return Response({"detail": "title and platform are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        title_q = normalize_title(title_q)

        all_prices = (
            RawPrice.objects.filter(search__user=request.user, platform=platform_q)
            .select_related("search")
            .order_by("scraped_at")
        )

        # Filter by normalized title
        matched = []
        for p in all_prices:
            if normalize_title(p.title) == title_q:
                matched.append(p)

        if not matched:
            return Response({"detail": "No data found for this product"}, status=status.HTTP_404_NOT_FOUND)

        # Build price history
        prices_mad = [round(float(p.price) * p.exchange_rate, 2) for p in matched]
        dates = [p.scraped_at for p in matched]

        price_history = [{"date": d.strftime("%Y-%m-%d"), "price_mad": pm} for d, pm in zip(dates, prices_mad)]

        # Summary
        current_price = prices_mad[-1]
        lowest_price = min(prices_mad)
        highest_price = max(prices_mad)
        lowest_idx = prices_mad.index(lowest_price)
        highest_idx = prices_mad.index(highest_price)
        avg_price = round(statistics.mean(prices_mad), 2)
        first_price = prices_mad[0]
        price_change = round(current_price - first_price, 2)
        price_change_pct = round((price_change / first_price) * 100, 1) if first_price else 0
        volatility = round(statistics.stdev(prices_mad), 2) if len(prices_mad) > 1 else 0
        days_tracked = (dates[-1] - dates[0]).days

        summary = {
            "current_price": current_price,
            "lowest_price": lowest_price,
            "lowest_price_date": dates[lowest_idx].strftime("%Y-%m-%d"),
            "highest_price": highest_price,
            "highest_price_date": dates[highest_idx].strftime("%Y-%m-%d"),
            "avg_price": avg_price,
            "total_scrapes": len(matched),
            "first_seen": dates[0].strftime("%Y-%m-%d"),
            "last_seen": dates[-1].strftime("%Y-%m-%d"),
            "price_change_overall": price_change,
            "price_change_percent": price_change_pct,
            "volatility": volatility,
            "days_tracked": days_tracked,
        }

        # Trend
        if len(prices_mad) < 3:
            trend = "uncertain"
        else:
            last3 = prices_mad[-3:]
            if last3[0] > last3[1] > last3[2]:
                trend = "dropping"
            elif last3[0] < last3[1] < last3[2]:
                trend = "rising"
            elif avg_price > 0 and (statistics.stdev(prices_mad) / avg_price) < 0.02:
                trend = "stable"
            else:
                trend = "fluctuating"

        # Recommendation
        if len(prices_mad) < 3:
            recommendation = {"verdict": "uncertain", "reason": "Not enough data yet. Scrape this product at least 3 times to get a recommendation."}
        elif current_price <= lowest_price * 1.05 and trend in ("dropping", "stable"):
            recommendation = {"verdict": "buy_now", "reason": "Current price is within 5% of the all-time low — this is near the best price ever recorded."}
        elif current_price <= avg_price * 0.90:
            recommendation = {"verdict": "good_deal", "reason": "Current price is more than 10% below the average — a better deal than usual."}
        elif trend == "rising" and current_price > avg_price:
            recommendation = {"verdict": "wait", "reason": "Price has been rising and is above average. Historical patterns suggest it may drop again."}
        elif trend == "dropping" and current_price > lowest_price * 1.10:
            recommendation = {"verdict": "wait", "reason": "Price is dropping. Wait a little longer — it may get closer to the all-time low."}
        else:
            recommendation = {"verdict": "neutral", "reason": "No strong signal either way. Monitor this product for a few more scrapes."}

        # Price brackets (3 brackets)
        min_p = min(prices_mad)
        max_p = max(prices_mad)
        bracket_range = (max_p - min_p) if max_p != min_p else 1
        bracket_size = bracket_range / 3
        brackets = [
            {"label": f"Under {round(min_p + bracket_size)} MAD", "min": min_p, "max": min_p + bracket_size, "count": 0},
            {"label": f"{round(min_p + bracket_size)}–{round(min_p + 2 * bracket_size)} MAD", "min": min_p + bracket_size, "max": min_p + 2 * bracket_size, "count": 0},
            {"label": f"Over {round(min_p + 2 * bracket_size)} MAD", "min": min_p + 2 * bracket_size, "max": max_p + 1, "count": 0},
        ]
        for pm in prices_mad:
            if pm < brackets[1]["min"]:
                brackets[0]["count"] += 1
            elif pm < brackets[2]["min"]:
                brackets[1]["count"] += 1
            else:
                brackets[2]["count"] += 1

        total = len(prices_mad)
        price_brackets = [{"label": b["label"], "count": b["count"], "percent": round(b["count"] / total * 100, 1)} for b in brackets]

        # Scrape log
        scrape_log = [{
            "date": p.scraped_at.strftime("%Y-%m-%d"),
            "price_mad": round(float(p.price) * p.exchange_rate, 2),
            "search_query": p.search.query,
            "product_url": p.url,
        } for p in matched]

        # Calendar data
        calendar_data = [{
            "date": d.strftime("%Y-%m-%d"),
            "price_mad": pm,
            "is_lowest": pm == lowest_price,
            "is_highest": pm == highest_price,
        } for d, pm in zip(dates, prices_mad)]

        # Threshold
        threshold_obj = PriceThreshold.objects.filter(
            user=request.user,
            normalized_title=title_q,
            platform=platform_q,
        ).first()
        threshold = {"threshold_mad": float(threshold_obj.threshold_mad)} if threshold_obj else None

        # Display title — most common raw title
        title_counter = Counter(p.title for p in matched)
        display_title = title_counter.most_common(1)[0][0]

        # Extract image_url from the latest scrape if available
        image_url = None
        for p in reversed(matched):
            if p.image_url:
                image_url = p.image_url
                break

        return Response({
            "title": display_title,
            "normalized_title": title_q,
            "platform": platform_q,
            "image_url": image_url,
            "trend": trend,
            "recommendation": recommendation,
            "summary": summary,
            "price_history": price_history,
            "price_brackets": price_brackets,
            "scrape_log": scrape_log,
            "calendar_data": calendar_data,
            "threshold": threshold,
        })


class SimilarProductsView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        title_q = request.query_params.get("title", "").strip()
        platform_q = request.query_params.get("platform", "").strip()

        if not title_q:
            return Response({"detail": "title is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        title_q = normalize_title(title_q)

        all_prices = RawPrice.objects.filter(search__user=request.user).select_related("search")

        # Build unique products
        products = {}
        for p in all_prices.iterator():
            norm = normalize_title(p.title)
            key = (norm, p.platform)
            if key == (title_q, platform_q):
                continue  # Skip the query product itself
            if key not in products:
                products[key] = {
                    "title": p.title,
                    "normalized_title": norm,
                    "platform": p.platform,
                    "prices": [],
                    "dates": [],
                }
            products[key]["prices"].append(float(p.price) * p.exchange_rate)
            products[key]["dates"].append(p.scraped_at)

        # Get current price of the query product
        current_product = RawPrice.objects.filter(
            search__user=request.user, platform=platform_q
        ).order_by("-scraped_at")
        current_price = None
        for p in current_product:
            if normalize_title(p.title) == title_q:
                current_price = float(p.price) * p.exchange_rate
                break

        # Score similarity
        scored = []
        for key, data in products.items():
            ratio = difflib.SequenceMatcher(None, title_q, data["normalized_title"]).ratio()
            if ratio > 0.45:
                latest_idx = data["dates"].index(max(data["dates"]))
                latest_price = round(data["prices"][latest_idx], 2)
                diff = round(latest_price - (current_price or 0), 2)
                direction = "cheaper" if diff < 0 else "more_expensive" if diff > 0 else "same"
                scored.append({
                    "title": data["title"],
                    "normalized_title": data["normalized_title"],
                    "platform": data["platform"],
                    "latest_price_mad": latest_price,
                    "price_diff_mad": round(abs(diff), 2),
                    "price_diff_direction": direction,
                    "scrape_count": len(data["prices"]),
                    "_ratio": ratio,
                })

        scored.sort(key=lambda x: x["_ratio"], reverse=True)
        for item in scored:
            del item["_ratio"]

        return Response(scored[:5])


class SetThresholdView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        norm_title = request.data.get("normalized_title", "").strip()
        platform = request.data.get("platform", "").strip()
        threshold_mad = request.data.get("threshold_mad")

        if not norm_title or not platform:
            return Response({"detail": "normalized_title and platform are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            threshold_mad = Decimal(str(threshold_mad))
            if threshold_mad <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"detail": "threshold_mad must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)

        obj, created = PriceThreshold.objects.update_or_create(
            user=request.user,
            normalized_title=norm_title,
            platform=platform,
            defaults={"threshold_mad": threshold_mad},
        )

        return Response({
            "normalized_title": obj.normalized_title,
            "platform": obj.platform,
            "threshold_mad": float(obj.threshold_mad),
            "created": created,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
