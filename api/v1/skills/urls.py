from django.urls import path
from .views import get_title_training_reports, get_training_report_by_id

urlpatterns = [
    path('reports/', get_title_training_reports, name='get-title-training-reports'),
    path('report/', get_training_report_by_id, name='get-training-report-by-id'),

]