from django.urls import path

from .views import (
    SearchDetailView,
    SearchListCreateView,
    SearchStatusView,
    SearchResultsView,
    SearchPCAView,
    SearchRulesView,
)

urlpatterns = [
    path("", SearchListCreateView.as_view(), name="search-list-create"),
    path("<int:pk>/", SearchDetailView.as_view(), name="search-detail"),
    path("<int:pk>/status/", SearchStatusView.as_view(), name="search-status"),
    path("<int:pk>/results/", SearchResultsView.as_view(), name="search-results"),
    path("<int:pk>/pca/", SearchPCAView.as_view(), name="search-pca"),
    path("<int:pk>/rules/", SearchRulesView.as_view(), name="search-rules"),
]
