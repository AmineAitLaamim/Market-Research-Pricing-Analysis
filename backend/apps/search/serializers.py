from rest_framework import serializers

from .models import Search


class SearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = (
            "id",
            "user",
            "query",
            "platforms",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "status", "created_at", "updated_at")

    def validate_platforms(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Platforms must be a non-empty list.")

        cleaned_platforms = []
        for platform in value:
            if not isinstance(platform, str) or not platform.strip():
                raise serializers.ValidationError(
                    "Each platform must be a non-empty string."
                )
            cleaned_platforms.append(platform.strip())

        return cleaned_platforms


class SearchCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = ("id", "query", "platforms", "status")
        read_only_fields = ("id", "status")

    def validate_platforms(self, value):
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Platforms must be a non-empty list.")
        return [str(p).strip() for p in value if str(p).strip()]


class SearchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = ("id", "query", "platforms", "status", "created_at")


class SearchStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Search
        fields = ("id", "status", "created_at")

from .models import RawPrice, AnalysisResult, AssociationRule

class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = ("cluster_kmeans", "cluster_dbscan", "is_anomaly", "deal_score", "pca_x", "pca_y")

class RawPriceSerializer(serializers.ModelSerializer):
    analysis = serializers.SerializerMethodField()
    price_mad = serializers.SerializerMethodField()

    class Meta:
        model = RawPrice
        fields = ("id", "platform", "title", "price", "currency", "exchange_rate", "price_mad", "url", "seller_rating", "condition", "analysis")

    def get_analysis(self, obj):
        res = obj.analysis_results.first()
        return AnalysisResultSerializer(res).data if res else None

    def get_price_mad(self, obj):
        return float(obj.price) * obj.exchange_rate

class AssociationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociationRule
        fields = ("antecedent", "consequent", "support", "confidence", "lift")
