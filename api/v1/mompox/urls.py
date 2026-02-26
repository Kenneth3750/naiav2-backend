from django.urls import path
from .views import (
    AboutMompoxInteligenteView,
    GetMompoxNewsView,
    GetMompoxTourismView,
    GetMompoxRestaurantsView,
    health_check,
    get_available_functions
)

urlpatterns = [
    # Main function endpoints
    path('about/', AboutMompoxInteligenteView.as_view(), name='mompox-about'),
    path('news/', GetMompoxNewsView.as_view(), name='mompox-news'),
    path('tourism/', GetMompoxTourismView.as_view(), name='mompox-tourism'),
    path('restaurants/', GetMompoxRestaurantsView.as_view(), name='mompox-restaurants'),

    # Utility endpoints
    path('health/', health_check, name='mompox-health'),
    path('functions/', get_available_functions, name='mompox-functions'),
]
