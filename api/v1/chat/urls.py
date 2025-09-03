from django.urls import path
from .views import Chat, ChatMessages, make_resume, upload_current_image, save_realtime_memory

urlpatterns = [
    path('', Chat.as_view(), name='chat'),
    path('messages/', ChatMessages.as_view(), name='chat-messages'),
    path('messages/resume/', make_resume, name='make-resume'),
    path('images/', upload_current_image, name='upload-current-image'),
    path('realtime/memory/', save_realtime_memory, name='save-realtime-memory'),
]