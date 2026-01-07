from django.contrib import admin
from amfi_downloader.models import DownloadLog


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    """
    Admin interface for DownloadLog model.
    Provides comprehensive view of all download attempts.
    """
    
    list_display = [
        'id',
        'month',
        'year',
        'status',
        'file_downloaded',
        'http_status_code',
        'api_triggered_at',
    ]
    
    list_filter = [
        'status',
        'file_downloaded',
        'month',
        'year',
        'api_triggered_at',
    ]
    
    search_fields = [
        'url',
        'month',
        'year',
        'error_message',
        'skip_reason',
    ]
    
    readonly_fields = [
        'url',
        'month',
        'year',
        'api_triggered_at',
        'http_status_code',
        'status',
        'file_downloaded',
        'file_path',
        'file_size_bytes',
        'skip_reason',
        'error_message',
        'created_at',
        'updated_at',
    ]
    
    ordering = ['-api_triggered_at']
    
    def has_add_permission(self, request):
        """Disable manual log creation via admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable log deletion via admin (audit trail)"""
        return False