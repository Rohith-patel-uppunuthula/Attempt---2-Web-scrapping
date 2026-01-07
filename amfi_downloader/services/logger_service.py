from amfi_downloader.models import DownloadLog
from django.utils import timezone


class LoggerService:
    """
    Centralized logging service for all download operations.
    Handles creation and querying of download logs.
    """
    
    @staticmethod
    def log_success(url, month, year, file_path, file_size, http_status):
        """
        Log a successful download.
        
        Args:
            url (str): Downloaded URL
            month (str): Month (e.g., 'jan')
            year (int): Year (e.g., 2025)
            file_path (str): Path where file was saved
            file_size (int): Size of downloaded file in bytes
            http_status (int): HTTP status code
        
        Returns:
            DownloadLog: Created log instance
        """
        log = DownloadLog.objects.create(
            url=url,
            month=month,
            year=year,
            api_triggered_at=timezone.now(),
            http_status_code=http_status,
            status=DownloadLog.SUCCESS,
            file_downloaded=True,
            file_path=file_path,
            file_size_bytes=file_size,
            skip_reason=None,
            error_message=None
        )
        return log
    
    @staticmethod
    def log_failure(url, month, year, http_status, error_message):
        """
        Log a failed download attempt.
        
        Args:
            url (str): Attempted URL
            month (str): Month (e.g., 'jan')
            year (int): Year (e.g., 2025)
            http_status (int): HTTP status code
            error_message (str): Error description
        
        Returns:
            DownloadLog: Created log instance
        """
        log = DownloadLog.objects.create(
            url=url,
            month=month,
            year=year,
            api_triggered_at=timezone.now(),
            http_status_code=http_status,
            status=DownloadLog.FAILED,
            file_downloaded=False,
            file_path=None,
            file_size_bytes=None,
            skip_reason=None,
            error_message=error_message
        )
        return log
    
    @staticmethod
    def log_skip(url, month, year, skip_reason):
        """
        Log a skipped download (already downloaded).
        
        Args:
            url (str): Skipped URL
            month (str): Month (e.g., 'jan')
            year (int): Year (e.g., 2025)
            skip_reason (str): Reason for skipping
        
        Returns:
            DownloadLog: Created log instance
        """
        log = DownloadLog.objects.create(
            url=url,
            month=month,
            year=year,
            api_triggered_at=timezone.now(),
            http_status_code=None,
            status=DownloadLog.SKIPPED,
            file_downloaded=False,
            file_path=None,
            file_size_bytes=None,
            skip_reason=skip_reason,
            error_message=None
        )
        return log
    
    @staticmethod
    def check_previous_success(url):
        """
        Check if URL was successfully downloaded before.
        
        Args:
            url (str): URL to check
        
        Returns:
            bool: True if already downloaded, False otherwise
        """
        return DownloadLog.has_successful_download(url)
    
    @staticmethod
    def get_last_successful_log(url):
        """
        Get the last successful download log for a URL.
        
        Args:
            url (str): URL to query
        
        Returns:
            DownloadLog or None: Last successful log if exists
        """
        return DownloadLog.get_last_successful_download(url)