from django.urls import path
from .views import (
    FrequentlyAskedQuestionsView,
    SearchTrafficFinesView,
    ExplainPassportProcessView,
    GetLocationEventsView,
    GetLocationPlacesView,
    health_check,
    get_available_functions
)

urlpatterns = [
    # Main function endpoints
    path('faq/', FrequentlyAskedQuestionsView.as_view(), name='gobernacion-faq'),
    path('traffic-fines/', SearchTrafficFinesView.as_view(), name='gobernacion-traffic-fines'),
    path('passport-process/', ExplainPassportProcessView.as_view(), name='gobernacion-passport-process'),
    path('events/', GetLocationEventsView.as_view(), name='gobernacion-events'),
    path('places/', GetLocationPlacesView.as_view(), name='gobernacion-places'),
    
    # Utility endpoints
    path('health/', health_check, name='gobernacion-health'),
    path('functions/', get_available_functions, name='gobernacion-functions'),
]