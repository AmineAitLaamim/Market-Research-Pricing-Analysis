from django.urls import path

from .views import (
    SearchDetailView,
    SearchListCreateView,
    SearchStatusView,
    SearchResultsView,
    SearchPCAView,
    SearchRulesView,
    RawPriceDetailView,
    AnalyticsView,
    CompareView,
    AlertListView,
    AlertMarkReadView,
    AlertMarkAllReadView,
)

urlpatterns = [
    path("", SearchListCreateView.as_view(), name="search-list-create"),
    path("compare/", CompareView.as_view(), name="search-compare"),
    path("analytics/", AnalyticsView.as_view(), name="search-analytics"),
    path("item/<int:pk>/", RawPriceDetailView.as_view(), name="item-detail"),
    path("<int:pk>/", SearchDetailView.as_view(), name="search-detail"),
    path("<int:pk>/status/", SearchStatusView.as_view(), name="search-status"),
    path("<int:pk>/results/", SearchResultsView.as_view(), name="search-results"),
    path("<int:pk>/pca/", SearchPCAView.as_view(), name="search-pca"),
    path("<int:pk>/rules/", SearchRulesView.as_view(), name="search-rules"),
    # Price alert endpoints
    path("alerts/", AlertListView.as_view(), name="alert-list"),
    path("alerts/<int:pk>/read/", AlertMarkReadView.as_view(), name="alert-mark-read"),
    path("alerts/read-all/", AlertMarkAllReadView.as_view(), name="alert-mark-all-read"),
]

