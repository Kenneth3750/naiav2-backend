from django.urls import path
from . import views

urlpatterns = [
    path('scholar-search/', views.search_academic_papers, name='scholar_search'),
    path('document/', views.create_document, name='create_document'),
    path('user-documents/', views.search_user_documents, name='search_user_documents'),
    path('web-search/', views.search_web, name='search_web'),
    path('graph/', views.generate_graph, name='generate_graph'),
    path('email/', views.send_user_email, name='send_user_email'),
    path('news/', views.get_current_news, name='get_current_news'),
    path('roles/', views.explain_roles, name='explain_roles'),
    path('deep-analysis/', views.deep_content_analysis, name='deep_content_analysis'),
]
