from django.urls import path
from .views import (
    UniGuideAnalysisView,
    WhyUninorteTopView,
    EngineeringOpportunitiesView,
    ElectricalEngineeringFutureView,
    InscriptionProcessView
)

urlpatterns = [
    path('form/analysis/', UniGuideAnalysisView.as_view(), name='form_analysis'),
    path('why-uninorte-top/', WhyUninorteTopView.as_view(), name='why_uninorte_top'),
    path('engineering-opportunities/', EngineeringOpportunitiesView.as_view(), name='engineering_opportunities'),
    path('electrical-engineering-future/', ElectricalEngineeringFutureView.as_view(), name='electrical_engineering_future'),
    path('inscription-process/', InscriptionProcessView.as_view(), name='inscription_process'),
]