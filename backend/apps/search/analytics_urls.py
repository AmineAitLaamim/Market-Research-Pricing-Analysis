from django.urls import path

from .analytics_views import (
    TopDropsView,
    ProductSearchView,
    ProductHistoryView,
    SimilarProductsView,
    SetThresholdView,
)

urlpatterns = [
    path("top-drops/", TopDropsView.as_view(), name="analytics-top-drops"),
    path("products/", ProductSearchView.as_view(), name="analytics-product-search"),
    path("product-history/", ProductHistoryView.as_view(), name="analytics-product-history"),
    path("similar/", SimilarProductsView.as_view(), name="analytics-similar"),
    path("threshold/", SetThresholdView.as_view(), name="analytics-threshold"),
]
