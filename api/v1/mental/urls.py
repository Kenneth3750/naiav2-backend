from django.urls import path
from .views import MentalAnalysisView

urlpatterns = [
    path('form/analysis/', MentalAnalysisView.as_view(), name='form_analysis'),
]