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
    """
    
    def __init__(self):
        self.url_generator = URLGenerator()
        self.logger = LoggerService()
        self.download_dir = settings.EXCEL_DOWNLOAD_DIR
    
    def execute_download(self):
        """
        Download current month (default behavior).
        """
        url_data = self.url_generator.generate_current_month_url()
        url = url_data['url']
        month = url_data['month']
        year = url_data['year']
        
        return self._process_download(url, month, year)
    
    def execute_download_for_date(self, month, year):
        """
        Download specific month/year.
        """
        # Validate month
        valid_months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                       'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        month = month.lower()
        if month not in valid_months:
            return {
                'status': 'error',
                'message': f'Invalid month: {month}. Must be one of: {", ".join(valid_months)}',
                'error': 'Invalid month'
            }
        
        # Generate URL for specific date
        url = self.url_generator.generate_url_for_date(month, year)
        
        return self._process_download(url, month, year)
    
    def _process_download(self, url, month, year):
        """
        Common logic for processing download + parse + store.
        """
        # Step 1: Idempotency check - check both download log AND database
        if self.logger.check_previous_success(url):
            # Also check if data actually exists in database
            month_label = ExcelParser._format_month_label(month, year)
            data_exists = AmfiMonthlyData.objects.filter(month=month_label).exists()
            
            if data_exists:
                # Already downloaded AND data exists, skip
                skip_reason = f"Already downloaded successfully on a previous API call"
                self.logger.log_skip(url, month, year, skip_reason)
                
                return {
                    'status': 'skipped',
                    'message': 'File already downloaded successfully and data exists in database',
                    'url': url,
                    'month': month,
                    'year': year,
                    'skip_reason': skip_reason,
                    'parsed_records': 0
                }
            else:
                # Downloaded but no data in DB - need to re-parse
                logger.info(f"File downloaded but no data in DB for {month} {year}, re-parsing...")
        
        # Step 2: Attempt download (or skip if file exists)
        download_result = self._download_file(url, month, year)
        
        # Step 3: If download succeeded, parse and store
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
        """
        try:
            response = requests.get(url, timeout=30, stream=True)
            
            if response.status_code == 200:
                filename = f"am{month}{year}repo.xls"
                file_path = os.path.join(self.download_dir, filename)
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                file_size = os.path.getsize(file_path)
                
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
                error_msg = f"HTTP {response.status_code}: File not available"
                self.logger.log_failure(url, month, year, response.status_code, error_msg)
                
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
        """
        try:
            parsed_data = ExcelParser.parse_excel(file_path, month, year)
            
            if not parsed_data:
                logger.warning(f"No data parsed from {file_path}")
                return {
                    'status': 'parse_failed',
                    'records_stored': 0,
                    'message': 'No data extracted from Excel file'
                }
            
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