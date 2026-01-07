from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from amfi_downloader.services import DownloadService
from amfi_downloader.serializers import DownloadResponseSerializer


class TriggerDownloadView(APIView):
    """
    API endpoint to trigger Excel file download.
    
    POST /api/download/trigger/
    
    This endpoint:
    1. Generates URL for current month
    2. Checks if already downloaded (idempotency)
    3. Downloads file if not already downloaded
    4. Logs everything
    
    Returns:
        JSON response with download status and details
    """
    
    def post(self, request):
        """
        Handle POST request to trigger download.
        
        No request body required - uses current date automatically.
        """
        try:
            # Initialize download service
            download_service = DownloadService()
            
            # Execute download workflow
            result = download_service.execute_download()
            
            # Serialize response
            serializer = DownloadResponseSerializer(data=result)
            serializer.is_valid(raise_exception=True)
            
            # Determine HTTP status code based on result
            if result['status'] == 'success':
                http_status = status.HTTP_200_OK
            elif result['status'] == 'skipped':
                http_status = status.HTTP_200_OK
            else:  # failed
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