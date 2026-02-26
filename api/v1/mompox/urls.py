from django.urls import path
from .views import (
    AboutMompoxInteligenteView,
    GetMompoxNewsView,
    health_check,
    get_available_functions
)

urlpatterns = [
    # Main function endpoints
    path('about/', AboutMompoxInteligenteView.as_view(), name='mompox-about'),
    path('news/', GetMompoxNewsView.as_view(), name='mompox-news'),

    # Utility endpoints
    path('health/', health_check, name='mompox-health'),
    path('functions/', get_available_functions, name='mompox-functions'),
]
