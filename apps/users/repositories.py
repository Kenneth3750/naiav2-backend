from .models import User
from django.db.utils import IntegrityError
import redis
from dotenv import load_dotenv
import os
load_dotenv()
class UserRepository:
    def get_user_by_id(self, user_id):
        return User.objects.get(id=user_id)
    def get_user_by_email(self, email):
        return User.objects.get(email=email)
    def create_user(self, name, family_name, email, photo_url):
        try:
            return User.objects.create(name=name, family_name=family_name, email=email, photo_url=photo_url)
        except IntegrityError:
            raise Exception(f"User with email {email} already exists")
    
    def get_user_by_email(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        
    def create_or_update_user_token(self, user_id, token):
        r = redis.Redis(
            host=os.getenv("redis_host"),
            port=os.getenv("redis_port"),
            db=os.getenv("redis_token_db"),
            decode_responses=True
        )
        r.set(f"user_token_{user_id}", token)

    def get_user_token(self, user_id):
        r = redis.Redis(
            host=os.getenv("redis_host"),
            port=os.getenv("redis_port"),
            db=os.getenv("redis_token_db"),
            decode_responses=True
        )
        return r.get(f"user_token_{user_id}")
    
