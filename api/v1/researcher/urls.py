from django.urls import path
from .views import ResearchDocumentView, save_document_changes


urlpatterns = [
    path('document/', ResearchDocumentView.as_view(), name='research-document'),
    path('document/save_changes/', save_document_changes, name='save-document-changes'),
]