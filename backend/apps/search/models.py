from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Search(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="searches",
    )
    query = models.CharField(max_length=500)
    platforms = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]


class RawPrice(models.Model):
    class Condition(models.TextChoices):
        NEW = "new", "New"
        LIKE_NEW = "like_new", "Like New"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"
        USED = "used", "Used"

    search = models.ForeignKey(
        Search,
        on_delete=models.CASCADE,
        related_name="raw_prices",
    )
    platform = models.CharField(max_length=50)
    title = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10)
    exchange_rate = models.FloatField()
    url = models.URLField(max_length=2000)
    image_url = models.URLField(max_length=2000, null=True, blank=True)
    seller_rating = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
    )
    condition = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=Condition.choices,
    )
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("search", "url")]
        indexes = [
            models.Index(fields=["search"]),
            models.Index(fields=["platform"]),
        ]


class AnalysisResult(models.Model):
    raw_price = models.ForeignKey(
        RawPrice,
        on_delete=models.CASCADE,
        related_name="analysis_results",
    )
    cluster_kmeans = models.IntegerField(null=True)
    cluster_dbscan = models.IntegerField(null=True)
    is_anomaly = models.BooleanField(default=False)
    deal_score = models.FloatField(null=True)
    pca_x = models.FloatField(null=True)
    pca_y = models.FloatField(null=True)


class SearchAnalysis(models.Model):
    search = models.ForeignKey(
        Search,
        on_delete=models.CASCADE,
        related_name="search_analyses",
    )
    stats = models.JSONField()
    best_deal = models.ForeignKey(
        RawPrice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="best_deal_for_search_analyses",
    )
    created_at = models.DateTimeField(auto_now_add=True)


class AssociationRule(models.Model):
    search = models.ForeignKey(
        Search,
        on_delete=models.CASCADE,
        related_name="association_rules",
    )
    antecedent = models.JSONField()
    consequent = models.JSONField()
    support = models.FloatField()
    confidence = models.FloatField()
    lift = models.FloatField()

    class Meta:
        indexes = [
            models.Index(fields=["search"]),
        ]


class PriceAlert(models.Model):
    user          = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="price_alerts",
    )
    product_title = models.CharField(max_length=500)
    old_price     = models.DecimalField(max_digits=10, decimal_places=2)
    new_price     = models.DecimalField(max_digits=10, decimal_places=2)
    drop_amount   = models.DecimalField(max_digits=10, decimal_places=2)
    drop_percent  = models.DecimalField(max_digits=5, decimal_places=1)
    platform      = models.CharField(max_length=100)
    product_url   = models.URLField(max_length=2000)
    search_query  = models.CharField(max_length=255)
    is_read       = models.BooleanField(default=False)
    is_threshold_alert = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]


class PriceThreshold(models.Model):
    user             = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="price_thresholds",
    )
    normalized_title = models.CharField(max_length=500)
    platform         = models.CharField(max_length=100)
    threshold_mad    = models.DecimalField(max_digits=10, decimal_places=2)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "normalized_title", "platform"]


