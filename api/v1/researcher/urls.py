from django.urls import path
from .views import upload_research_document


urlpatterns = [
    path('document/', upload_research_document, name='upload-research-document'),
]