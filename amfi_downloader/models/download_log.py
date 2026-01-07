from django.db import models
from django.utils import timezone


class DownloadLog(models.Model):
    """
    Model to track every download attempt for Excel files.
    Ensures idempotency and provides complete audit trail.
    """
    
    # URL and identification
    url = models.URLField(max_length=500, db_index=True)
    month = models.CharField(max_length=3)  # jan, feb, mar, etc.
    year = models.IntegerField()
    
    # Timestamps
    api_triggered_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    # HTTP Response
    http_status_code = models.IntegerField(null=True, blank=True)
    
    # Outcome
    SUCCESS = 'success'
    FAILED = 'failed'
    SKIPPED = 'skipped'
    
    STATUS_CHOICES = [
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
        (SKIPPED, 'Skipped'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        db_index=True
    )
    
    # File information
    file_downloaded = models.BooleanField(default=False)
    file_path = models.CharField(max_length=500, null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Skip/Error details
    skip_reason = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'download_logs'
        ordering = ['-api_triggered_at']
        indexes = [
            models.Index(fields=['url', 'status']),
            models.Index(fields=['month', 'year']),
            models.Index(fields=['api_triggered_at']),
        ]
    
    def __str__(self):
        return f"{self.month}{self.year} - {self.status} - {self.api_triggered_at}"
    
    @classmethod
    def get_last_successful_download(cls, url):
        """
        Get the last successful download log for a given URL.
        Used for idempotency checks.
        """
        return cls.objects.filter(
            url=url,
            status=cls.SUCCESS,
            file_downloaded=True
        ).first()
    
    @classmethod
    def has_successful_download(cls, url):
        """
        Check if URL has been successfully downloaded before.
        Returns True if already downloaded, False otherwise.
        """
        return cls.objects.filter(
            url=url,
            status=cls.SUCCESS,
            file_downloaded=True
        ).exists()