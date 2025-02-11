from django.urls import path, include
from .views import Chat
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('', Chat.as_view(), name='chat'),
]