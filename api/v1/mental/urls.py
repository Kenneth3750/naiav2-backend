from django.urls import path
from .views import (
    MentalAnalysisView,
    GetAlternativasDeportivasView,
    GetCatalogoActividadesView,
    GetFlexibilidadInfoView,
    health_check,
    get_available_functions
)

urlpatterns = [
    # Legacy
    path('form/analysis/', MentalAnalysisView.as_view(), name='form_analysis'),

    # Bienestar Organizacional endpoints
    path('alternativas/', GetAlternativasDeportivasView.as_view(), name='biela-alternativas'),
    path('catalogo/', GetCatalogoActividadesView.as_view(), name='biela-catalogo'),
    path('flexibilidad/', GetFlexibilidadInfoView.as_view(), name='biela-flexibilidad'),

    # Utility
    path('health/', health_check, name='biela-health'),
    path('functions/', get_available_functions, name='biela-functions'),
]
