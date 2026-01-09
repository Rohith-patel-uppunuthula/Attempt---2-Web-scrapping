from django.urls import path
from amfi_downloader.views import (
    TriggerDownloadView,
    YearMatrixView,
    YearSummaryView,
    MonthDetailView
)

app_name = 'amfi_downloader'

urlpatterns = [
    # Download trigger endpoint
    path('download/trigger/', TriggerDownloadView.as_view(), name='trigger_download'),
    
    # AMFI Data APIs
    path('amfi/year/<int:year>/', YearMatrixView.as_view(), name='year_matrix'),
    path('amfi/year/<int:year>/summary/', YearSummaryView.as_view(), name='year_summary'),
    path('amfi/month/<str:month>/', MonthDetailView.as_view(), name='month_detail'),
]