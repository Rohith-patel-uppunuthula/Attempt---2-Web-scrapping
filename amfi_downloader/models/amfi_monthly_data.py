from django.db import models


class AmfiMonthlyData(models.Model):
    """
    Model to store parsed AMFI mutual fund data.
    Each row represents one scheme's net inflow for a specific month.
    """
    
    # Month in format: "01-May-25" or "January 2025"
    month = models.CharField(max_length=50, db_index=True)
    
    # Scheme category (e.g., "Small Cap Fund", "Large Cap Fund")
    scheme_category = models.CharField(max_length=200, db_index=True)
    
    # Net inflow value (can be positive or negative)
    net_inflow = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'amfi_monthly_data'
        ordering = ['month', 'scheme_category']
        unique_together = ['month', 'scheme_category']  # Prevent duplicates
        indexes = [
            models.Index(fields=['month']),
            models.Index(fields=['scheme_category']),
            models.Index(fields=['month', 'scheme_category']),
        ]
    
    def __str__(self):
        return f"{self.month} - {self.scheme_category}: {self.net_inflow}"
    
    @classmethod
    def get_year_data(cls, year):
        """
        Get all data for a specific year.
        Year can be 2025, 2026, etc.
        """
        return cls.objects.filter(month__contains=str(year))
    
    @classmethod
    def get_month_data(cls, month):
        """
        Get all schemes for a specific month.
        """
        return cls.objects.filter(month=month)