from rest_framework import serializers
from amfi_downloader.models import AmfiMonthlyData


class AmfiMonthlyDataSerializer(serializers.ModelSerializer):
    """
    Serializer for individual AMFI monthly data records.
    """
    class Meta:
        model = AmfiMonthlyData
        fields = ['id', 'month', 'scheme_category', 'net_inflow', 'created_at', 'updated_at']
        read_only_fields = fields


class SchemeDataSerializer(serializers.Serializer):
    """
    Serializer for scheme data (used in API responses).
    """
    scheme = serializers.CharField()
    net_inflow = serializers.DecimalField(max_digits=15, decimal_places=2)


class MonthDetailSerializer(serializers.Serializer):
    """
    Serializer for API 3: Individual month data.
    Returns all schemes for a specific month.
    """
    month = serializers.CharField()
    data = SchemeDataSerializer(many=True)


class MonthlySummaryItemSerializer(serializers.Serializer):
    """
    Serializer for single month summary (Small Cap + Large/Midcap).
    """
    month = serializers.CharField()
    small_cap = serializers.DecimalField(max_digits=15, decimal_places=2)
    large_midcap = serializers.DecimalField(max_digits=15, decimal_places=2)


class YearSummarySerializer(serializers.Serializer):
    """
    Serializer for API 2: Year summary (aggregated).
    Returns Small Cap + Large/Midcap for all months in a year.
    """
    year = serializers.IntegerField()
    data = MonthlySummaryItemSerializer(many=True)


class YearMatrixSerializer(serializers.Serializer):
    """
    Serializer for API 1: Year matrix (category-wise monthly values).
    Returns all schemes across all months in dashboard format.
    """
    year = serializers.IntegerField()
    months = serializers.ListField(child=serializers.CharField())
    categories = serializers.ListField(child=serializers.CharField())
    data = serializers.DictField()