from django.urls import path
from .views import StatusView

urlpatterns = [
    path('', StatusView.as_view(), name='status'),
]