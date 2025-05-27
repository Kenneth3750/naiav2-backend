from django.urls import path
from .views import UniGuideAnalysisView

urlpatterns = [
    path('form/analysis/', UniGuideAnalysisView.as_view(), name='form_analysis'),
]