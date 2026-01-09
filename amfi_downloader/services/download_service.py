import os
import requests
from django.conf import settings
from .url_generator import URLGenerator
from .logger_service import LoggerService
from .excel_parser import ExcelParser
from amfi_downloader.models import AmfiMonthlyData
import logging

logger = logging.getLogger(__name__)


class DownloadService:
    """
    Core service for downloading Excel files with idempotency checks.
    Now includes parsing and storing data in database.
    
    Workflow:
    1. Generate URL for current month
    2. Check if already downloaded (idempotency)
    3. Download file if needed
    4. Parse Excel file
    5. Store parsed data in database
    6. Log everything
    """
    
    def __init__(self):
        self.url_generator = URLGenerator()
        self.logger = LoggerService()
        self.download_dir = settings.EXCEL_DOWNLOAD_DIR
    
    def execute_download(self):
        """
        Main execution method called by API endpoint.
        
        Returns:
            dict: Result summary with status and details
        """
        # Step 1: Generate URL for current month
        url_data = self.url_generator.generate_current_month_url()
        url = url_data['url']
        month = url_data['month']
        year = url_data['year']
        
        # Step 2: Idempotency check
        if self.logger.check_previous_success(url):
            # Already downloaded successfully, skip
            skip_reason = f"Already downloaded successfully on a previous API call"
            self.logger.log_skip(url, month, year, skip_reason)
            
            return {
                'status': 'skipped',
                'message': 'File already downloaded successfully',
                'url': url,
                'month': month,
                'year': year,
                'skip_reason': skip_reason,
                'parsed_records': 0
            }
        
        # Step 3: Attempt download
        download_result = self._download_file(url, month, year)
        
        # Step 4: If download succeeded, parse and store
        if download_result['status'] == 'success':
            parse_result = self._parse_and_store(
                download_result['file_path'],
                month,
                year
            )
            download_result['parsed_records'] = parse_result['records_stored']
            download_result['parse_status'] = parse_result['status']
        
        return download_result
    
    def _download_file(self, url, month, year):
        """
        Download file from URL and save to disk.
        
        Args:
            url (str): URL to download
            month (str): Month (e.g., 'jan')
            year (int): Year (e.g., 2025)
        
        Returns:
            dict: Download result with status and details
        """
        try:
            # Make HTTP request with timeout
            response = requests.get(url, timeout=30, stream=True)
            
            # Check if file exists (HTTP 200)
            if response.status_code == 200:
                # Generate filename
                filename = f"am{month}{year}repo.xls"
                file_path = os.path.join(self.download_dir, filename)
                
                # Save file to disk
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Log success
                self.logger.log_success(
                    url=url,
                    month=month,
                    year=year,
                    file_path=file_path,
                    file_size=file_size,
                    http_status=response.status_code
                )
                
                return {
                    'status': 'success',
                    'message': 'File downloaded successfully',
                    'url': url,
                    'month': month,
                    'year': year,
                    'file_path': file_path,
                    'file_size_bytes': file_size,
                    'http_status': response.status_code
                }
            
            else:
                # File doesn't exist or error occurred
                error_msg = f"HTTP {response.status_code}: File not available"
                
                # Log failure
                self.logger.log_failure(
                    url=url,
                    month=month,
                    year=year,
                    http_status=response.status_code,
                    error_message=error_msg
                )
                
                return {
                    'status': 'failed',
                    'message': error_msg,
                    'url': url,
                    'month': month,
                    'year': year,
                    'http_status': response.status_code,
                    'error': error_msg
                }
        
        except requests.exceptions.Timeout:
            error_msg = "Request timeout: Server took too long to respond"
            self.logger.log_failure(url, month, year, None, error_msg)
            
            return {
                'status': 'failed',
                'message': error_msg,
                'url': url,
                'month': month,
                'year': year,
                'error': error_msg
            }
        
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error: Unable to reach server"
            self.logger.log_failure(url, month, year, None, error_msg)
            
            return {
                'status': 'failed',
                'message': error_msg,
                'url': url,
                'month': month,
                'year': year,
                'error': error_msg
            }
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.log_failure(url, month, year, None, error_msg)
            
            return {
                'status': 'failed',
                'message': error_msg,
                'url': url,
                'month': month,
                'year': year,
                'error': error_msg
            }
    
    def _parse_and_store(self, file_path, month, year):
        """
        Parse downloaded Excel file and store data in database.
        
        Args:
            file_path (str): Path to downloaded Excel file
            month (str): Month (e.g., 'jan')
            year (int): Year (e.g., 2025)
        
        Returns:
            dict: Parse result with status and count
        """
        try:
            # Parse Excel file
            parsed_data = ExcelParser.parse_excel(file_path, month, year)
            
            if not parsed_data:
                logger.warning(f"No data parsed from {file_path}")
                return {
                    'status': 'parse_failed',
                    'records_stored': 0,
                    'message': 'No data extracted from Excel file'
                }
            
            # Store in database
            records_stored = 0
            for record in parsed_data:
                AmfiMonthlyData.objects.update_or_create(
                    month=record['month'],
                    scheme_category=record['scheme'],
                    defaults={'net_inflow': record['net_inflow']}
                )
                records_stored += 1
            
            logger.info(f"Stored {records_stored} records in database")
            
            return {
                'status': 'parse_success',
                'records_stored': records_stored,
                'message': f'Successfully parsed and stored {records_stored} records'
            }
        
        except Exception as e:
            logger.error(f"Error parsing/storing data: {str(e)}")
            return {
                'status': 'parse_error',
                'records_stored': 0,
                'message': f'Error: {str(e)}'
            }