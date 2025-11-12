from django.urls import path
from . import views

urlpatterns = [
    path('contacts/', views.search_contacts, name='search_contacts'),
    path('premises/', views.get_premises_info, name='get_premises_info'),
    path('menus/', views.search_menus, name='search_menus'),
    path('events/', views.find_events, name='find_events'),
    path('restaurants/', views.find_restaurants, name='find_restaurants'),
    path('places/', views.discover_places, name='discover_places'),
    path('email/', views.send_info_email, name='send_info_email'),
]
