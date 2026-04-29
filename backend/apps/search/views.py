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
from django.db.models import F

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
