from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from amfi_downloader.models import AmfiMonthlyData
from amfi_downloader.serializers import (
    MonthDetailSerializer,
    YearSummarySerializer,
    YearMatrixSerializer
)


# ======================================================
# CONFIG: Large & Midcap Bucket
# ======================================================

LARGE_MIDCAP_BUCKET = [
    "LARGE CAP FUND",
    "MID CAP FUND",
    "LARGE & MID CAP FUND",
    "FLEXI CAP FUND",
    "FOCUSED FUND",
    "VALUE FUND/CONTRA FUND",
    "DIVIDEND YIELD FUND",
    "ELSS",
    "SECTORAL/THEMATIC FUNDS",
    "MULTI CAP FUND",
]


# ======================================================
# HELPER FUNCTION
# ======================================================

def get_year_suffix(year):
    """
    Convert 4-digit year to 2-digit suffix.
    Example: 2025 -> '25', 2026 -> '26'
    """
    return str(year)[-2:]


# ======================================================
# API 1: Year Matrix (Category-wise Monthly Values)
# ======================================================

class YearMatrixView(APIView):
    """
    GET /api/amfi/year/<year>/
    """
    
    def get(self, request, year):
        try:
            year = int(year)
        except ValueError:
            return Response(
                {"error": "Invalid year format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert to 2-digit year suffix
        year_suffix = get_year_suffix(year)
        
        # Get all data for the year
        qs = AmfiMonthlyData.objects.filter(month__contains=f'-{year_suffix}')
        
        if not qs.exists():
            return Response(
                {"error": f"No data found for year {year}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get unique months (convert to set to remove duplicates)
        months = sorted(list(set(qs.values_list('month', flat=True))))
        
        # Get unique categories (convert to set to remove duplicates)
        categories = sorted(list(set(qs.values_list('scheme_category', flat=True))))
        
        # Build matrix: {month: {category: net_inflow}}
        data_matrix = {}
        for month in months:
            data_matrix[month] = {}
        
        # Populate matrix
        for record in qs:
            data_matrix[record.month][record.scheme_category] = float(record.net_inflow)
        
        response_data = {
            'year': year,
            'months': months,
            'categories': categories,
            'data': data_matrix
        }
        
        serializer = YearMatrixSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ======================================================
# API 2: Year Summary (Small Cap + Large/Midcap Aggregated)
# ======================================================

class YearSummaryView(APIView):
    """
    GET /api/amfi/year/<year>/summary/
    """
    
    def get(self, request, year):
        try:
            year = int(year)
        except ValueError:
            return Response(
                {"error": "Invalid year format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert to 2-digit year suffix
        year_suffix = get_year_suffix(year)
        
        # Get all data for the year
        qs = AmfiMonthlyData.objects.filter(month__contains=f'-{year_suffix}')
        
        if not qs.exists():
            return Response(
                {"error": f"No data found for year {year}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get unique months (convert to set to remove duplicates)
        months = sorted(list(set(qs.values_list('month', flat=True))))
        
        # Calculate Small Cap + Large/Midcap for each month
        summary_data = []
        for month in months:
            month_qs = qs.filter(month=month)
            
            # Small Cap
            small_cap = month_qs.filter(
                scheme_category="SMALL CAP FUND"
            ).aggregate(total=Sum('net_inflow'))['total'] or 0
            
            # Large & Midcap (all except Small Cap)
            large_midcap = month_qs.filter(
                scheme_category__in=LARGE_MIDCAP_BUCKET
            ).aggregate(total=Sum('net_inflow'))['total'] or 0
            
            summary_data.append({
                'month': month,
                'small_cap': round(float(small_cap), 2),
                'large_midcap': round(float(large_midcap), 2)
            })
        
        response_data = {
            'year': year,
            'data': summary_data
        }
        
        serializer = YearSummarySerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ======================================================
# API 3: Individual Month Data
# ======================================================

class MonthDetailView(APIView):
    """
    GET /api/amfi/month/<month>/
    
    Returns all schemes for a specific month.
    
    Example:
        GET /api/amfi/month/01-Apr-25/
    """
    
    def get(self, request, month):
        # Get all data for the month
        qs = AmfiMonthlyData.objects.filter(month=month)
        
        if not qs.exists():
            return Response(
                {"error": f"No data found for month {month}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Build response data
        schemes_data = []
        for record in qs:
            schemes_data.append({
                'scheme': record.scheme_category,
                'net_inflow': float(record.net_inflow)
            })
        
        response_data = {
            'month': month,
            'data': schemes_data
        }
        
        serializer = MonthDetailSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)