from apps.users.models import User
from apps.chat.models import Roles
from .models import Chat
from django.utils import timezone
import redis
from dotenv import load_dotenv
import os
class ChatRepository:
    @staticmethod
    def get_last_conversation(user, role_id):
        messages = Chat.objects.filter(user_id=user, rol=role_id).order_by('-created_at').first()
        return messages.message if messages else None
    
    def _get_last_chat(user_id, role_id):
        return Chat.objects.filter(user_id=user_id, rol=role_id).order_by('-created_at').first()

    @staticmethod
    def update_or_create_today_conversation(user_id, message_data, role_id):
        today = timezone.now().date()
        user = User.objects.get(id=user_id)
        role = Roles.objects.get(id=role_id)
        last_chat= ChatRepository._get_last_chat(user_id, role_id)
        
        if last_chat and last_chat.created_at.date() == today:
            last_chat.message = message_data.decode('utf-8') if isinstance(message_data, bytes) else message_data
            last_chat.save()
            return last_chat, False
        
        
        return Chat.objects.create(
            user_id=user,
            message=message_data.decode('utf-8') if isinstance(message_data, bytes) else message_data,
            rol=role
        
        ), True
    
    @staticmethod
    def get_user_conversation(user):
        """Get all conversations for a user"""
        return Chat.objects.filter(user_id=user).order_by('-created_at')
    
    @staticmethod
    def save_current_conversation(user_id, role_id, messages):
        load_dotenv()
        r = redis.Redis(host=os.getenv("redis_host"), port=os.getenv("redis_port"), db=os.getenv("redis_db"))
        r.set(f"current_conversation_{user_id}_{role_id}", messages)
        r.close()

    @staticmethod
    def delete_current_conversation(user_id, role_id):
        load_dotenv()
        r = redis.Redis(host=os.getenv("redis_host"), port=os.getenv("redis_port"),  db=os.getenv("redis_db"))        
        r.delete(f"current_conversation_{user_id}_{role_id}")
        r.close()
    
    @staticmethod
    def get_current_conversation(user_id, role_id):
        load_dotenv()
        r = redis.Redis(host=os.getenv("redis_host"), port=os.getenv("redis_port"),  db=os.getenv("redis_db"))
        conversation = r.get(f"current_conversation_{user_id}_{role_id}")
        r.close()
        return conversation

