from rest_framework import serializers
from amfi_downloader.models import DownloadLog


class DownloadLogSerializer(serializers.ModelSerializer):
    """
    Serializer for DownloadLog model.
    Used for API responses.
    """
    
    class Meta:
        model = DownloadLog
        fields = [
            'id',
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
            'updated_at'
        ]
        read_only_fields = fields  # All fields are read-only


class DownloadResponseSerializer(serializers.Serializer):
    """
    Serializer for download operation response.
    Used to structure API responses consistently.
    """
    status = serializers.ChoiceField(
        choices=['success', 'failed', 'skipped']
    )
    message = serializers.CharField()
    url = serializers.URLField()
    month = serializers.CharField()
    year = serializers.IntegerField()
    file_path = serializers.CharField(required=False, allow_null=True)
    file_size_bytes = serializers.IntegerField(required=False, allow_null=True)
    http_status = serializers.IntegerField(required=False, allow_null=True)
    skip_reason = serializers.CharField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)