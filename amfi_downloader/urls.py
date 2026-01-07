from django.urls import path
from amfi_downloader.views import TriggerDownloadView

app_name = 'amfi_downloader'

urlpatterns = [
    path('download/trigger/', TriggerDownloadView.as_view(), name='trigger_download'),
]