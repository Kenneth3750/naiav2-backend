from django.urls import path
from . import views

urlpatterns = [
    path('rag-query/', views.university_rag_query, name='university_rag_query'),
    path('calendar/', views.get_campus_calendar, name='get_campus_calendar'),
    path('tour/', views.virtual_campus_tour, name='virtual_campus_tour'),
    path('search/', views.search_university_internet, name='search_university_internet'),
    path('email/', views.send_university_email, name='send_university_email'),
    path('contacts/', views.search_university_contacts, name='search_university_contacts'),
    path('calendar-event/', views.create_university_calendar_event, name='create_university_calendar_event'),
]
