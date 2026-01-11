from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from amfi_downloader.services import DownloadService
from amfi_downloader.serializers import DownloadResponseSerializer


class TriggerDownloadView(APIView):
    """
    API endpoint to trigger Excel file download.
    
    POST /api/download/trigger/
    POST /api/download/trigger/?month=apr&year=2025
    
    Query Parameters (optional):
        - month: Month in short form (jan, feb, mar, etc.)
        - year: 4-digit year (e.g., 2025)
    
    If no parameters provided, downloads current month.
    
    This endpoint:
    1. Generates URL (current month or specific month/year)
    2. Checks if already downloaded (idempotency)
    3. Downloads file if not already downloaded
    4. Parses Excel and stores in database
    5. Logs everything
    
    Returns:
        JSON response with download status and details
    """
    
    def post(self, request):
        """
        Handle POST request to trigger download.
        
        Query parameters (optional):
            - month: Month in short form (e.g., 'apr')
            - year: 4-digit year (e.g., 2025)
        
        If no parameters, uses current date automatically.
        """
        try:
            # Get optional query parameters
            month = request.query_params.get('month')
            year = request.query_params.get('year')
            
            # Initialize download service
            download_service = DownloadService()
            
            # Execute download workflow
            if month and year:
                # Download specific month/year
                try:
                    year = int(year)
                    result = download_service.execute_download_for_date(month, year)
                except ValueError:
                    return Response(
                        {
                            'status': 'error',
                            'message': 'Invalid year format. Must be a number (e.g., 2025)'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Download current month (default behavior)
                result = download_service.execute_download()
            
            # Serialize response
            serializer = DownloadResponseSerializer(data=result)
            serializer.is_valid(raise_exception=True)
            
            # Determine HTTP status code based on result
            if result['status'] == 'success':
                http_status = status.HTTP_200_OK
            elif result['status'] == 'skipped':
                http_status = status.HTTP_200_OK
            else:  # failed or error
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            return Response(
                serializer.validated_data,
                status=http_status
            )
        
        except Exception as e:
            # Catch any unexpected errors
            return Response(
                {
                    'status': 'error',
                    'message': 'An unexpected error occurred',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )