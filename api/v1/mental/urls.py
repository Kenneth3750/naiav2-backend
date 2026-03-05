from django.urls import path
from .views import (
    MentalAnalysisView,
    GetAlternativasDeportivasView,
    GetCatalogoActividadesView,
    GetFlexibilidadInfoView,
    GetVirtualCampusTourView,
    send_email_view,
    search_contacts_view,
    create_event_view,
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
    path('tour/', GetVirtualCampusTourView.as_view(), name='biela-tour'),
    path('send-email/', send_email_view, name='biela-send-email'),
    path('search-contacts/', search_contacts_view, name='biela-search-contacts'),
    path('create-event/', create_event_view, name='biela-create-event'),

    # Utility
    path('health/', health_check, name='biela-health'),
    path('functions/', get_available_functions, name='biela-functions'),
]
