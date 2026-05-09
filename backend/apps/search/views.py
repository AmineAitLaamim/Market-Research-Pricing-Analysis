from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .filters import SearchFilter
from .models import Search
from .serializers import (
    SearchCreateSerializer,
    SearchListSerializer,
    SearchSerializer,
    SearchStatusSerializer,
)
from .tasks import run_search_pipeline


class SearchListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = SearchFilter

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SearchCreateSerializer
        return SearchListSerializer

    def get_queryset(self):
        return Search.objects.filter(user=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query = serializer.validated_data["query"]
        platforms = serializer.validated_data["platforms"]

        # 1. Deduplication Logic
        # Filter by user, query and active status first (fast database query)
        potential_searches = Search.objects.filter(
            user=request.user,
            query__iexact=query,
            status__in=[Search.Status.PENDING, Search.Status.PROCESSING]
        )
        
        # Check platforms in Python to ensure SQLite compatibility (JSONField __contains not supported)
        existing_search = None
        target_platforms = sorted(platforms)
        for s in potential_searches:
            if sorted(s.platforms) == target_platforms:
                existing_search = s
                break

        if existing_search:
            # Return existing search with 200 OK
            out_serializer = SearchCreateSerializer(existing_search)
            return Response(out_serializer.data, status=status.HTTP_200_OK)

        # 2. Create new search
        search = serializer.save(user=request.user, status=Search.Status.PENDING)
        
        # 3. Dispatch Celery Task
        run_search_pipeline.delay(search.id)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SearchDetailView(generics.RetrieveAPIView):
    serializer_class = SearchSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Search.objects.filter(user=self.request.user)


class SearchStatusView(generics.RetrieveAPIView):
    serializer_class = SearchStatusSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Search.objects.filter(user=self.request.user)

from rest_framework.pagination import PageNumberPagination
from .models import RawPrice, SearchAnalysis, AssociationRule
from .serializers import RawPriceSerializer, AssociationRuleSerializer
from django.db.models import F, Count, Avg, FloatField, ExpressionWrapper
from django.db.models.functions import TruncDate

class ResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000

class SearchResultsView(generics.ListAPIView):
    serializer_class = RawPriceSerializer
    pagination_class = ResultsPagination
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = RawPrice.objects.filter(search_id=self.kwargs["pk"], search__user=self.request.user).prefetch_related("analysis_results")
        platform = self.request.query_params.get("platform")
        is_anomaly = self.request.query_params.get("is_anomaly")
        ordering = self.request.query_params.get("ordering")
        
        if platform:
            qs = qs.filter(platform=platform)
        if is_anomaly == "true":
            qs = qs.filter(analysis_results__is_anomaly=True)
            
        if ordering == "-analysis__deal_score":
            qs = qs.annotate(deal_score=F("analysis_results__deal_score")).order_by("-deal_score", "price")
        elif ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("price")
            
        return qs

    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        if self.request.query_params.get("page", "1") == "1":
            analysis = SearchAnalysis.objects.filter(search_id=self.kwargs["pk"]).first()
            if analysis:
                best_deal_data = RawPriceSerializer(analysis.best_deal).data if analysis.best_deal else None
                response.data["meta"] = {
                    "stats": analysis.stats,
                    "best_deal": best_deal_data
                }
        return response

class SearchPCAView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, pk):
        items = RawPrice.objects.filter(search_id=pk, search__user=request.user).prefetch_related("analysis_results")
        results = []
        for item in items:
            an = item.analysis_results.first()
            if an and (an.pca_x is not None and an.pca_y is not None):
                results.append({
                    "id": item.id,
                    "title": item.title,
                    "platform": item.platform,
                    "price_mad": float(item.price) * item.exchange_rate,
                    "url": item.url,
                    "pca_x": an.pca_x,
                    "pca_y": an.pca_y,
                    "is_anomaly": an.is_anomaly,
                    "deal_score": an.deal_score,
                    "cluster_kmeans": an.cluster_kmeans,
                })
        return Response(results)

class SearchRulesView(generics.ListAPIView):
    serializer_class = AssociationRuleSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return AssociationRule.objects.filter(search_id=self.kwargs["pk"], search__user=self.request.user)

class RawPriceDetailView(generics.RetrieveAPIView):
    serializer_class = RawPriceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = RawPrice.objects.all()

class AnalyticsView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # 1. Summary Metrics
        total_searches = Search.objects.filter(user=user).count()
        total_items = RawPrice.objects.filter(search__user=user).count()
        avg_items = total_items / total_searches if total_searches > 0 else 0
        
        most_searched = Search.objects.filter(user=user).values("query").annotate(count=Count("id")).order_by("-count").first()
        most_searched_keyword = most_searched["query"] if most_searched else "N/A"

        # 2. Price Trend Chart
        trends = (
            RawPrice.objects.filter(search__user=user)
            .annotate(date=TruncDate("scraped_at"))
            .values("date", "platform")
            .annotate(avg_price=Avg(F("price") * F("exchange_rate"), output_field=FloatField()))
            .order_by("date")
        )
        
        trend_data = {}
        for t in trends:
            # handle cases where date might be None just in case
            if not t["date"]: continue
            date_str = t["date"].strftime("%Y-%m-%d")
            platform = t["platform"]
            avg_price = round(t["avg_price"], 2) if t["avg_price"] else 0
            if date_str not in trend_data:
                trend_data[date_str] = {"date": date_str}
            trend_data[date_str][platform] = avg_price
        
        trend_list = sorted(list(trend_data.values()), key=lambda x: x["date"])

        # 3. Top Cheapest Products
        cheapest_products = (
            RawPrice.objects.filter(search__user=user)
            .annotate(price_mad=ExpressionWrapper(F("price") * F("exchange_rate"), output_field=FloatField()))
            .order_by("price_mad")[:5]
        )
        cheapest_data = [
            {
                "id": p.id,
                "title": p.title,
                "platform": p.platform,
                "price_mad": round(p.price_mad, 2) if p.price_mad else 0,
                "url": p.url,
            } for p in cheapest_products
        ]

        # 4. Keyword Frequency
        keywords = (
            Search.objects.filter(user=user)
            .values("query")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        keyword_data = [{"keyword": k["query"], "count": k["count"]} for k in keywords]

        return Response({
            "summary": {
                "total_searches": total_searches,
                "total_items": total_items,
                "avg_items_per_search": round(avg_items, 1),
                "most_searched_keyword": most_searched_keyword,
            },
            "price_trends": trend_list,
            "top_cheap_products": cheapest_data,
            "keyword_frequency": keyword_data,
        })

import difflib
import re

def normalize_title(title):
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    return ' '.join(title.split())

class CompareView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        a_id = request.query_params.get('a')
        b_id = request.query_params.get('b')

        if not a_id or not b_id:
            return Response({"detail": "Missing parameters a or b"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            search_a = Search.objects.get(id=a_id, user=request.user)
            search_b = Search.objects.get(id=b_id, user=request.user)
        except Search.DoesNotExist:
            return Response({"detail": "Search not found or permission denied"}, status=status.HTTP_404_NOT_FOUND)

        if search_a.query.lower() != search_b.query.lower():
            return Response({"detail": "Cannot compare searches with different queries"}, status=status.HTTP_400_BAD_REQUEST)

        prices_a = list(RawPrice.objects.filter(search=search_a))
        prices_b = list(RawPrice.objects.filter(search=search_b))

        dict_a = {normalize_title(p.title): p for p in prices_a}
        dict_b = {normalize_title(p.title): p for p in prices_b}

        matched = []
        new_items = []
        gone_items = []

        for norm_a, p_a in dict_a.items():
            if norm_a in dict_b:
                p_b = dict_b[norm_a]
                matched.append({
                    "id_a": p_a.id, "id_b": p_b.id,
                    "title": p_a.title,
                    "platform": p_a.platform,
                    "price_a": round(float(p_a.price) * p_a.exchange_rate, 2),
                    "price_b": round(float(p_b.price) * p_b.exchange_rate, 2),
                    "diff": round((float(p_b.price) * p_b.exchange_rate) - (float(p_a.price) * p_a.exchange_rate), 2),
                    "url_a": p_a.url,
                    "url_b": p_b.url,
                })
                del dict_b[norm_a]
            else:
                best_match = None
                best_ratio = 0
                for norm_b in list(dict_b.keys()):
                    ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
                    if ratio > 0.85 and ratio > best_ratio:
                        best_ratio = ratio
                        best_match = norm_b
                
                if best_match:
                    p_b = dict_b[best_match]
                    matched.append({
                        "id_a": p_a.id, "id_b": p_b.id,
                        "title": p_a.title,
                        "platform": p_a.platform,
                        "price_a": round(float(p_a.price) * p_a.exchange_rate, 2),
                        "price_b": round(float(p_b.price) * p_b.exchange_rate, 2),
                        "diff": round((float(p_b.price) * p_b.exchange_rate) - (float(p_a.price) * p_a.exchange_rate), 2),
                        "url_a": p_a.url,
                        "url_b": p_b.url,
                    })
                    del dict_b[best_match]
                else:
                    gone_items.append({
                        "id": p_a.id,
                        "title": p_a.title,
                        "platform": p_a.platform,
                        "price_a": round(float(p_a.price) * p_a.exchange_rate, 2),
                        "url_a": p_a.url,
                    })
        
        for norm_b, p_b in dict_b.items():
            new_items.append({
                "id": p_b.id,
                "title": p_b.title,
                "platform": p_b.platform,
                "price_b": round(float(p_b.price) * p_b.exchange_rate, 2),
                "url_b": p_b.url,
            })

        avg_a = sum(float(p.price) * p.exchange_rate for p in prices_a) / len(prices_a) if prices_a else 0
        avg_b = sum(float(p.price) * p.exchange_rate for p in prices_b) / len(prices_b) if prices_b else 0
        
        cheapest_a = min(prices_a, key=lambda p: float(p.price) * p.exchange_rate) if prices_a else None
        cheapest_b = min(prices_b, key=lambda p: float(p.price) * p.exchange_rate) if prices_b else None

        dist_data_a = [round(float(p.price) * p.exchange_rate, 2) for p in prices_a]
        dist_data_b = [round(float(p.price) * p.exchange_rate, 2) for p in prices_b]

        return Response({
            "query": search_a.query,
            "date_a": search_a.created_at.strftime("%Y-%m-%d"),
            "date_b": search_b.created_at.strftime("%Y-%m-%d"),
            "summary": {
                "avg_price_a": round(avg_a, 2),
                "avg_price_b": round(avg_b, 2),
                "total_items_a": len(prices_a),
                "total_items_b": len(prices_b),
                "cheapest_a": round(float(cheapest_a.price) * cheapest_a.exchange_rate, 2) if cheapest_a else None,
                "cheapest_b": round(float(cheapest_b.price) * cheapest_b.exchange_rate, 2) if cheapest_b else None,
                "new_items_count": len(new_items),
                "gone_items_count": len(gone_items),
            },
            "matched": matched,
            "new_items": new_items,
            "gone_items": gone_items,
            "prices_a": dist_data_a,
            "prices_b": dist_data_b,
        })

from .models import PriceAlert

class AlertListView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        alerts = PriceAlert.objects.filter(user=request.user)
        unread_count = alerts.filter(is_read=False).count()
        data = [
            {
                "id": a.id,
                "product_title": a.product_title,
                "old_price": str(a.old_price),
                "new_price": str(a.new_price),
                "drop_amount": str(a.drop_amount),
                "drop_percent": str(a.drop_percent),
                "platform": a.platform,
                "product_url": a.product_url,
                "search_query": a.search_query,
                "is_read": a.is_read,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ]
        return Response({"unread_count": unread_count, "results": data})


class AlertMarkReadView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, pk):
        try:
            alert = PriceAlert.objects.get(pk=pk, user=request.user)
        except PriceAlert.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        alert.is_read = True
        alert.save(update_fields=["is_read"])
        return Response({"id": alert.id, "is_read": True})


class AlertMarkAllReadView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request):
        updated = PriceAlert.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"marked": updated})

