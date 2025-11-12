from django.urls import path
from . import views

urlpatterns = [
    path('news/', views.get_news, name='get_news'),
    path('weather/', views.get_weather_info, name='get_weather'),
    path('email/', views.send_email, name='send_email'),
    path('contacts/', views.search_contacts, name='search_contacts'),
    path('calendar/', views.read_calendar, name='read_calendar'),
    path('calendar-event/', views.create_event, name='create_event'),
    path('emails/', views.read_emails, name='read_emails'),
    path('roles/', views.explain_roles, name='explain_roles'),
]
