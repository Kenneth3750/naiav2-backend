from django.urls import path, include
from .views import Chat, ChatMessages
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('', Chat.as_view(), name='chat'),
    path('messages/', ChatMessages.as_view(), name='chat-messages'),
]