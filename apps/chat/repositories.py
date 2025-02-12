from django.db import models
from django.contrib.auth.models import User
from .models import Chat
from django.utils import timezone

class ChatRepository:
    @staticmethod
    def get_last_conversation(user):
        return Chat.objects.filter(user_id=user).order_by('-created_at').first()
    
    @staticmethod
    def get_or_create_today_conversation(user, message_data, rol):
        today = timezone.now().date()
        last_chat= ChatRepository.get_last_conversation(user)
        
        if last_chat and last_chat.created_at.date() == today:
            last_chat.message = message_data
            last_chat.rol = rol
            last_chat.save()
            return last_chat, False
        
        #create new conversation
        return Chat.objects.create(
            user_id=user,
            message=message_data,
            rol=rol
        
        ), True
    
    @staticmethod
    def get_user_conversation(user):
        """Get all conversations for a user"""
        return Chat.objects.filter(user_id=user).order_by('-created_at')

